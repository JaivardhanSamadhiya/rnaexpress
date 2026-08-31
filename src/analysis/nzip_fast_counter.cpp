#include <zlib.h>

#include <algorithm>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <limits>
#include <string>
#include <unordered_map>
#include <unordered_set>
#include <utility>
#include <vector>

namespace {

constexpr const char* kAdapter = "TTCGATATCCGCATGCTAGC";
constexpr int kAdapterLength = 20;

struct LibraryEntry {
    std::string id;
    std::string sequence;
};

struct Metrics {
    std::uint64_t fastq_reads = 0;
    std::uint64_t no_adapter = 0;
    std::uint64_t umi_n = 0;
    std::uint64_t no_match = 0;
    std::uint64_t multi_match = 0;
    std::uint64_t single_match = 0;
    std::uint64_t mismatch_counts[5] = {0, 0, 0, 0, 0};
};

std::vector<LibraryEntry> load_fasta(const std::string& path) {
    std::ifstream input(path);
    if (!input) throw std::runtime_error("Cannot open FASTA: " + path);
    std::vector<LibraryEntry> entries;
    std::string line;
    LibraryEntry current;
    while (std::getline(input, line)) {
        if (!line.empty() && line.back() == '\r') line.pop_back();
        if (line.empty()) continue;
        if (line[0] == '>') {
            if (!current.id.empty()) entries.push_back(std::move(current));
            current = LibraryEntry{line.substr(1), ""};
        } else {
            current.sequence += line;
        }
    }
    if (!current.id.empty()) entries.push_back(std::move(current));
    if (entries.empty()) throw std::runtime_error("FASTA contains no entries");
    return entries;
}

bool gz_readline(gzFile handle, std::string& output) {
    output.clear();
    char buffer[4096];
    while (true) {
        char* result = gzgets(handle, buffer, sizeof(buffer));
        if (result == nullptr) return !output.empty();
        output += buffer;
        if (!output.empty() && output.back() == '\n') {
            output.pop_back();
            if (!output.empty() && output.back() == '\r') output.pop_back();
            return true;
        }
        if (gzeof(handle)) return true;
    }
}

int find_adapter(const std::string& read) {
    if (read.size() < kAdapterLength) return -1;
    for (std::size_t offset = 0; offset + kAdapterLength <= read.size(); ++offset) {
        int mismatches = 0;
        for (int position = 0; position < kAdapterLength; ++position) {
            if (read[offset + position] != kAdapter[position] && ++mismatches > 2) break;
        }
        if (mismatches <= 2) return static_cast<int>(offset);
    }
    return -1;
}

std::string block_key(int block, const std::string& value) {
    return static_cast<char>('0' + block) + value;
}

int mismatch_score(const std::string& observed, const std::string& expected) {
    const std::size_t length = std::min(observed.size(), expected.size());
    int total = 0;
    int seed = 0;
    for (std::size_t position = 0; position < length; ++position) {
        if (observed[position] != expected[position]) {
            ++total;
            if (position < 15 && ++seed > 2) return -1;
            if (total >= 5) return -1;
        }
    }
    return total;
}

void add_candidates(
    const std::vector<int>& source,
    std::vector<std::uint32_t>& marks,
    std::uint32_t generation,
    std::vector<int>& candidates
) {
    for (int index : source) {
        if (marks[index] != generation) {
            marks[index] = generation;
            candidates.push_back(index);
        }
    }
}

void write_json_metrics(const std::string& path, const Metrics& metrics) {
    std::ofstream output(path);
    if (!output) throw std::runtime_error("Cannot write metrics: " + path);
    output << "{\n"
           << "  \"fastq_reads\": " << metrics.fastq_reads << ",\n"
           << "  \"adapter_absent\": " << metrics.no_adapter << ",\n"
           << "  \"umi_contains_n_skipped\": " << metrics.umi_n << ",\n"
           << "  \"adapter_positive_unmapped\": " << metrics.no_match << ",\n"
           << "  \"ambiguous_best_sequence_tie\": " << metrics.multi_match << ",\n"
           << "  \"uniquely_mapped_reads\": " << metrics.single_match << ",\n"
           << "  \"mapped_mismatches_0\": " << metrics.mismatch_counts[0] << ",\n"
           << "  \"mapped_mismatches_1\": " << metrics.mismatch_counts[1] << ",\n"
           << "  \"mapped_mismatches_2\": " << metrics.mismatch_counts[2] << ",\n"
           << "  \"mapped_mismatches_3\": " << metrics.mismatch_counts[3] << ",\n"
           << "  \"mapped_mismatches_4\": " << metrics.mismatch_counts[4] << "\n"
           << "}\n";
}

}  // namespace

int main(int argc, char** argv) {
    try {
        if (argc != 6) {
            std::cerr << "Usage: nzip_fast_counter LIBRARY.fa READS.fastq.gz OUT.tsv METRICS.json MAX_RECORDS\n";
            return 2;
        }
        const std::string fasta_path = argv[1];
        const std::string fastq_path = argv[2];
        const std::string output_path = argv[3];
        const std::string metrics_path = argv[4];
        const std::uint64_t max_records = std::stoull(argv[5]);

        const auto library = load_fasta(fasta_path);
        std::unordered_map<std::string, std::vector<int>> block_index;
        std::unordered_map<std::string, std::vector<int>> seed_index;
        for (int index = 0; index < static_cast<int>(library.size()); ++index) {
            const std::string& sequence = library[index].sequence;
            if (sequence.size() < 80) throw std::runtime_error("Library sequence shorter than 80 nt");
            for (int block = 0; block < 5; ++block) {
                block_index[block_key(block, sequence.substr(block * 16, 16))].push_back(index);
            }
            for (int start = 0; start <= 10; ++start) {
                seed_index[sequence.substr(start, 5)].push_back(index);
            }
        }

        std::vector<std::uint64_t> read_counts(library.size(), 0);
        std::vector<std::unordered_set<std::string>> umi_sets(library.size());
        // Audit-only strict channel.  The primary columns retain the exact
        // source-equivalent <=4-mismatch behavior validated against the jar.
        std::vector<std::uint64_t> exact_read_counts(library.size(), 0);
        std::vector<std::unordered_set<std::string>> exact_umi_sets(library.size());
        std::vector<std::uint32_t> marks(library.size(), 0);
        std::uint32_t generation = 0;
        Metrics metrics;

        gzFile fastq = gzopen(fastq_path.c_str(), "rb");
        if (fastq == nullptr) throw std::runtime_error("Cannot open FASTQ: " + fastq_path);
        std::string header, read, plus, quality;
        std::vector<int> candidates;
        while ((max_records == 0 || metrics.fastq_reads < max_records) &&
               gz_readline(fastq, header)) {
            if (!gz_readline(fastq, read) || !gz_readline(fastq, plus) || !gz_readline(fastq, quality)) {
                int zlib_error = Z_OK;
                const char* zlib_message = gzerror(fastq, &zlib_error);
                gzclose(fastq);
                throw std::runtime_error(
                    "Truncated FASTQ record after " + std::to_string(metrics.fastq_reads) +
                    " complete records; zlib=" + std::to_string(zlib_error) + " " +
                    (zlib_message == nullptr ? std::string("") : std::string(zlib_message))
                );
            }
            ++metrics.fastq_reads;
            const int adapter_offset = find_adapter(read);
            if (adapter_offset < 0) {
                ++metrics.no_adapter;
                continue;
            }
            const std::string umi = read.substr(0, adapter_offset);
            if (umi.find('N') != std::string::npos) {
                ++metrics.umi_n;
                continue;
            }
            const std::string payload = read.substr(adapter_offset + kAdapterLength);

            ++generation;
            if (generation == 0) {
                std::fill(marks.begin(), marks.end(), 0);
                generation = 1;
            }
            candidates.clear();
            if (payload.size() >= 80) {
                for (int block = 0; block < 5; ++block) {
                    auto found = block_index.find(block_key(block, payload.substr(block * 16, 16)));
                    if (found != block_index.end()) add_candidates(found->second, marks, generation, candidates);
                }
            } else if (payload.size() >= 5) {
                const int stop = static_cast<int>(std::min<std::size_t>(payload.size(), 15)) - 5;
                for (int start = 0; start <= stop; ++start) {
                    auto found = seed_index.find(payload.substr(start, 5));
                    if (found != seed_index.end()) add_candidates(found->second, marks, generation, candidates);
                }
            }

            int best_score = std::numeric_limits<int>::max();
            int best_index = -1;
            int best_count = 0;
            for (int index : candidates) {
                const int score = mismatch_score(payload, library[index].sequence);
                if (score < 0) continue;
                if (score < best_score) {
                    best_score = score;
                    best_index = index;
                    best_count = 1;
                } else if (score == best_score) {
                    ++best_count;
                }
            }
            if (best_count == 0) {
                ++metrics.no_match;
            } else if (best_count > 1) {
                ++metrics.multi_match;
            } else {
                ++metrics.single_match;
                ++metrics.mismatch_counts[best_score];
                ++read_counts[best_index];
                umi_sets[best_index].insert(umi);
                if (best_score == 0) {
                    ++exact_read_counts[best_index];
                    exact_umi_sets[best_index].insert(umi);
                }
            }
        }
        gzclose(fastq);

        std::ofstream output(output_path);
        if (!output) throw std::runtime_error("Cannot write counts: " + output_path);
        output << "sequence_id\tread_count\tdistinct_umi_count"
                  "\texact_read_count\texact_distinct_umi_count\n";
        for (int index = 0; index < static_cast<int>(library.size()); ++index) {
            output << library[index].id << '\t' << read_counts[index] << '\t'
                   << umi_sets[index].size() << '\t' << exact_read_counts[index] << '\t'
                   << exact_umi_sets[index].size() << '\n';
        }
        write_json_metrics(metrics_path, metrics);
        std::cout << "reads=" << metrics.fastq_reads << " single=" << metrics.single_match
                  << " umi=";
        std::uint64_t umi_total = 0;
        for (const auto& values : umi_sets) umi_total += values.size();
        std::cout << umi_total << "\n";
        return 0;
    } catch (const std::exception& error) {
        std::cerr << error.what() << '\n';
        return 1;
    }
}
