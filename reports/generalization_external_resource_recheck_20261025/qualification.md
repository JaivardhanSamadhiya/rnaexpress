# SECReTE: metadata verified; external benchmark still unqualified

The official [bioRxiv metadata API](https://api.biorxiv.org/details/biorxiv/10.64898/2026.10.12.758471)
and [Crossref DOI endpoint](https://api.crossref.org/works/10.64898/2026.10.12.758471)
returned public, unauthenticated HTTP 200 responses. Whitelisted metadata is
saved with response hashes and request times in `public_api_probe_01.json`.
The API lists version 1 dated 13 October 2026 and version 2 dated 14 October
2026, and supplies the official version-specific JATS links. Its article
license is CC BY-NC-ND; that alone does not establish a raw dataset's license.

One request to the API-supplied version-2 XML link returned HTTP 429, preserved
in `source_xml_probe_01.json`. No XML or outcome dataset was downloaded; further
requests to that host were stopped. This is an access limitation, not evidence
that data are absent or unavailable to the public.

The indexed abstract makes this a relevant localization/reporter-library lead.
Admission still requires verified data accession/files, their public/free
provenance and reuse terms, replicate structure, full library ancestry and
whether the library contains suitable small-edit comparisons. No library size
or biological effect from an abstract certifies those conditions. No new test
set, raw outcomes, model selection or research claim is admitted by these probes.

The nuclear-speckle paper (10.1093/nar/gkag174) was already assessed in the
project's literature, novelty and small-edit audits. Its rediscovery is not a
new independent benchmark or evidence of project novelty. Its outcomes were
not reopened during this check.
