"""Exact changed-site masks and conditional-marginal arithmetic, stdlib only."""
from dataclasses import dataclass
import hashlib
import math

IDS = {'A':6, 'C':7, 'G':8, 'T':9}
MASK = 4


def dna(value):
    assert isinstance(value, str) and value and set(value) <= set(IDS), 'Exact uppercase A/C/G/T DNA required'
    assert len(value) <= 1024
    return value


@dataclass(frozen=True)
class Request:
    parent: str
    mutant: str
    positions: tuple
    input_ids: tuple
    reference_ids: tuple
    alternate_ids: tuple

    @property
    def context_sha256(self):
        return hashlib.sha256(bytes(self.input_ids)).hexdigest()


def request(parent, mutant):
    parent, mutant = dna(parent), dna(mutant)
    assert len(parent) == len(mutant), 'Only equal-length substitutions'
    positions = tuple(i for i,(a,b) in enumerate(zip(parent,mutant)) if a != b)
    assert len(positions) <= 6, 'Fixed scope is no-edit or one-to-six substitutions'
    tokens = [2] + [IDS[base] for base in parent] + [3]
    for p in positions:
        tokens[p + 1] = MASK
    masked_mutant = [2] + [IDS[base] for base in mutant] + [3]
    for p in positions:
        masked_mutant[p + 1] = MASK
    assert tokens == masked_mutant, 'Non-edited context must be identical'
    return Request(parent, mutant, positions, tuple(tokens), tuple(IDS[parent[p]] for p in positions), tuple(IDS[mutant[p]] for p in positions))


def model_inputs(requests):
    assert requests and len({len(r.input_ids) for r in requests}) == 1, 'Group identical lengths; no fake sequence padding'
    assert all(r == request(r.parent,r.mutant) for r in requests), 'Reject noncanonical masks/positions/allele metadata'
    rows = [list(r.input_ids) for r in requests]
    assert all(row[0] == 2 and row[-1] == 3 and 0 not in row and 1 not in row and 5 not in row for row in rows)
    return {'input_ids':rows, 'attention_mask':[[1]*len(row) for row in rows], 'token_type_ids':[[0]*len(row) for row in rows]}


def batches(requests):
    """Fixed batch2 per exact length; duplicate final real context, then discard."""
    assert all(r == request(r.parent,r.mutant) for r in requests)
    lengths = sorted({len(r.input_ids) for r in requests if r.positions})
    for length in lengths:
        selected = [r for r in requests if r.positions and len(r.input_ids) == length]
        for first in range(0,len(selected),2):
            batch = selected[first:first+2]
            real = len(batch)
            if real == 1:
                batch.append(batch[0])
            yield batch, real


def log_softmax(logits):
    value = list(map(float,logits))
    assert len(value) == 10 and all(math.isfinite(x) for x in value), 'All ten finite vocabulary logits required'
    maximum = max(value)
    shifted = [x-maximum for x in value]
    assert all(math.isfinite(x) for x in shifted), 'Finite representable log differences required'
    normalizer = math.log(math.fsum(math.exp(x) for x in shifted))
    return [x-normalizer for x in shifted]


def score(r, logits=None):
    assert r == request(r.parent,r.mutant), 'Reject inconsistent mask/changed-site/allele metadata'
    if not r.positions:
        assert r.parent == r.mutant
        return {'score':0., 'per_edit':[], 'changed_sites':0, 'context_sha256':r.context_sha256}
    assert logits is not None and len(logits) == len(r.input_ids)
    assert all(len(row) == 10 and all(math.isfinite(float(x)) for x in row) for row in logits)
    edits = []
    for p,ref,alt in zip(r.positions,r.reference_ids,r.alternate_ids):
        row = list(map(float,logits[p+1]));logs = log_softmax(row)
        # Same masked context/position: the ten-token normalizer cancels exactly
        # in real arithmetic. Direct subtraction avoids large-normalizer loss.
        ratio = row[alt]-row[ref]
        assert math.isfinite(ratio)
        assert math.isclose(logs[alt]-logs[ref],ratio,rel_tol=1e-12,abs_tol=1e-12)
        edits.append({'position_zero_based':p,'token_position':p+1,'reference_token':ref,'alternate_token':alt,'logp_reference':logs[ref],'logp_alternate':logs[alt],'log_ratio':ratio})
    return {'score':math.fsum(e['log_ratio'] for e in edits),'per_edit':edits,'changed_sites':len(edits),'context_sha256':r.context_sha256}


def evaluate(requests, predictor):
    result = {r:score(r) for r in requests if not r.positions}
    for batch, real in batches(requests):
        output = predictor(model_inputs(batch))
        assert len(output) == 2
        for r,logits in zip(batch[:real],output[:real]):
            result[r] = score(r,logits)
    return [result[r] for r in requests]


def synthetic_sequences(left, right):
    """Byte-identical copied original 16-allele invented recipe; no lookup."""
    assert len(left) == len(right) == 20 and set(left+right) <= set(IDS)
    result = []
    for length in (46,150,190,260):
        for replicate in range(2):
            seed = ('splicebert_backend_20261007:'+str(length)+':'+str(replicate)).encode()
            core = 6 if length == 46 else length
            bases = ''.join('ACGT'[hashlib.sha256(seed+i.to_bytes(4,'little')).digest()[0]%4] for i in range(core))
            parent = left+bases+right if length == 46 else bases
            p = 23 if length == 46 else length//2
            mutant = parent[:p]+'ACGT'[('ACGT'.index(parent[p])+1)%4]+parent[p+1:]
            result.extend((parent,mutant))
    assert len(result) == len(set(result)) == 16
    return result


def additional_synthetic_requests(original):
    """Fixed boundary/multisite arithmetic roster; never replace original16."""
    result = []
    for parent in original[::4]:
        for count in (2,3,4,5,6):
            positions = [0,len(parent)-1]+list(range(1,count-1))
            mutant = list(parent)
            for p in positions:
                mutant[p] = 'ACGT'[('ACGT'.index(parent[p])+1)%4]
            result.append(request(parent,''.join(mutant)))
    assert len(result) == 20
    return result
