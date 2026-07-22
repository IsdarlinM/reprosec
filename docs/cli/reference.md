# CLI Reference — reprosec v0.3.0

Generated from the registered command surface. Every registered command below uses the same Click/Typer command tree used at runtime.

## Root help

```text
Usage: reprosec [OPTIONS] COMMAND [ARGS]...

  ReproSec Capsule — capture, sanitize, verify and replay evidence.

Options:
  --install-completion  Install completion for the current shell.
  --show-completion     Show completion for the current shell, to copy it or
                        customize the installation.
  -h, --help            Show this message and exit.

Commands:
  version
  init           Create a new unpacked RCAP workspace.
  inspect        Inspect capsule metadata and file counts without...
  assertion      Add a deterministic assertion.
  pack           Create a deterministic .rcap ZIP container and manifest.
  verify         Verify schema-facing manifest hashes and optional...
  sign           Build the manifest and sign it with a local Ed25519...
  replay         Replay one request through Scope -> Policy -> Rate Limit...
  check          Evaluate one deterministic assertion against one stored...
  redact         Preview or apply secret redaction to stored...
  diff           Compare two responses without printing sensitive body...
  capture        Capture one authorized HTTP interaction through the same...
  extract        Run a deterministic header/cookie/regex/JSONPath extractor.
  timeline       Show a deterministic evidence timeline without inferring...
  explain        Show evidence lineage for a request without converting...
  matrix         Build an observed actor/operation matrix from stored...
  sync-lineage   Index RCAP requests/responses/workflow into SRIC lineage...
  research-note  List or append a reproducible research-notebook entry...
  query          Search the SRIC graph previously produced by `reprosec...
  conformance    Run RCAP layout, integrity and deterministic-pack...
  report         Export a report that separates evidence from...
  doctor         Check runtime, dependencies, safe defaults and optional...
  update         Check or install a signed wheel release; never performs...
  web            Run the local API.
  demo           Create an offline synthetic two-actor capsule that...
  help           Show root or top-level command help.
  import         Import HAR, raw HTTP or curl into a capsule directory.
  workflow       Build deterministic multi-actor workflow steps.
  key            Generate and use local Ed25519 signing keys.
```

## `reprosec assertion`

```text
Usage: reprosec assertion [OPTIONS] CAPSULE REQUEST_ID KIND EXPECTED

  Add a deterministic assertion. Use --selector for header/JSONPath
  assertions.

Arguments:
  CAPSULE     [required]
  REQUEST_ID  [required]
  KIND        [required]
  EXPECTED    [required]

Options:
  --selector TEXT
  -h, --help       Show this message and exit.
```

## `reprosec capture`

```text
Usage: reprosec capture [OPTIONS] CAPSULE URL

  Capture one authorized HTTP interaction through the same safe replay gates.

Arguments:
  CAPSULE  [required]
  URL      [required]

Options:
  --allow TEXT          [required]
  --method TEXT         [default: GET]
  --allow-network TEXT
  --allow-method TEXT   [default: GET, HEAD, OPTIONS]
  --approve-action
  --follow-redirects
  -h, --help            Show this message and exit.
```

## `reprosec check`

```text
Usage: reprosec check [OPTIONS] CAPSULE ASSERTION_ID RESPONSE_ID

  Evaluate one deterministic assertion against one stored response.

Arguments:
  CAPSULE       [required]
  ASSERTION_ID  [required]
  RESPONSE_ID   [required]

Options:
  -h, --help  Show this message and exit.
```

## `reprosec conformance`

```text
Usage: reprosec conformance [OPTIONS] CAPSULE

  Run RCAP layout, integrity and deterministic-pack conformance checks.

Arguments:
  CAPSULE  [required]

Options:
  -h, --help  Show this message and exit.
```

## `reprosec demo`

```text
Usage: reprosec demo [OPTIONS]

  Create an offline synthetic two-actor capsule that demonstrates evidence
  lineage.

Options:
  --output PATH  [default: reprosec-demo]
  -h, --help     Show this message and exit.
```

## `reprosec diff`

```text
Usage: reprosec diff [OPTIONS] CAPSULE EXPECTED_RESPONSE_ID
                     OBSERVED_RESPONSE_ID

  Compare two responses without printing sensitive body content.

Arguments:
  CAPSULE               [required]
  EXPECTED_RESPONSE_ID  [required]
  OBSERVED_RESPONSE_ID  [required]

Options:
  --semantic
  -h, --help  Show this message and exit.
```

## `reprosec doctor`

```text
Usage: reprosec doctor [OPTIONS]

  Check runtime, dependencies, safe defaults and optional network
  prerequisites.

Options:
  --network        Diagnose DNS/proxy/network prerequisites without replaying
                   a target request.
  --dns-name TEXT  [default: example.com]
  -h, --help       Show this message and exit.
```

## `reprosec explain`

```text
Usage: reprosec explain [OPTIONS] CAPSULE REQUEST_ID

  Show evidence lineage for a request without converting inference into a
  finding.

Arguments:
  CAPSULE     [required]
  REQUEST_ID  [required]

Options:
  -h, --help  Show this message and exit.
```

## `reprosec extract`

```text
Usage: reprosec extract [OPTIONS] CAPSULE RESPONSE_ID NAME KIND SELECTOR

  Run a deterministic header/cookie/regex/JSONPath extractor.

Arguments:
  CAPSULE      [required]
  RESPONSE_ID  [required]
  NAME         [required]
  KIND         [required]
  SELECTOR     [required]

Options:
  --sensitive
  --save-spec / --no-save-spec  [default: save-spec]
  --reveal                      Explicitly print a sensitive extracted value.
  -h, --help                    Show this message and exit.
```

## `reprosec help`

```text
Usage: reprosec help [OPTIONS] [COMMAND]

  Show root or top-level command help.

Arguments:
  [COMMAND]

Options:
  -h, --help  Show this message and exit.
```

## `reprosec import`

```text
Usage: reprosec import [OPTIONS] COMMAND [ARGS]...

  Import HAR, raw HTTP or curl into a capsule directory.

Options:
  -h, --help  Show this message and exit.

Commands:
  har   Import requests/responses from a HAR.
  raw   Import a raw HTTP request without executing it.
  curl  Parse a constrained curl command as data; the command is never...
```

## `reprosec import curl`

```text
Usage: reprosec import curl [OPTIONS] COMMAND

  Parse a constrained curl command as data; the command is never executed.

Arguments:
  COMMAND  [required]

Options:
  --capsule PATH  [required]
  -h, --help      Show this message and exit.
```

## `reprosec import har`

```text
Usage: reprosec import har [OPTIONS] PATH

  Import requests/responses from a HAR. Sensitive headers are redacted.

Arguments:
  PATH  [required]

Options:
  --capsule PATH  [required]
  -h, --help      Show this message and exit.
```

## `reprosec import raw`

```text
Usage: reprosec import raw [OPTIONS] PATH

  Import a raw HTTP request without executing it.

Arguments:
  PATH  [required]

Options:
  --capsule PATH  [required]
  --scheme TEXT   [default: https]
  --host TEXT
  -h, --help      Show this message and exit.
```

## `reprosec init`

```text
Usage: reprosec init [OPTIONS] PATH

  Create a new unpacked RCAP workspace.

Arguments:
  PATH  [required]

Options:
  --title TEXT  [required]
  -h, --help    Show this message and exit.
```

## `reprosec inspect`

```text
Usage: reprosec inspect [OPTIONS] CAPSULE

  Inspect capsule metadata and file counts without replaying traffic.

Arguments:
  CAPSULE  [required]

Options:
  -h, --help  Show this message and exit.
```

## `reprosec key`

```text
Usage: reprosec key [OPTIONS] COMMAND [ARGS]...

  Generate and use local Ed25519 signing keys.

Options:
  -h, --help  Show this message and exit.

Commands:
  generate  Generate a local Ed25519 keypair.
```

## `reprosec key generate`

```text
Usage: reprosec key generate [OPTIONS]

  Generate a local Ed25519 keypair. Private keys are never uploaded.

Options:
  --private PATH  [required]
  --public PATH   [required]
  -h, --help      Show this message and exit.
```

## `reprosec matrix`

```text
Usage: reprosec matrix [OPTIONS] CAPSULE

  Build an observed actor/operation matrix from stored evidence only.

Arguments:
  CAPSULE  [required]

Options:
  -h, --help  Show this message and exit.
```

## `reprosec pack`

```text
Usage: reprosec pack [OPTIONS] CAPSULE

  Create a deterministic .rcap ZIP container and manifest.

Arguments:
  CAPSULE  [required]

Options:
  --output PATH  [required]
  -h, --help     Show this message and exit.
```

## `reprosec query`

```text
Usage: reprosec query [OPTIONS] CAPSULE QUERY

  Search the SRIC graph previously produced by `reprosec sync-lineage`.

Arguments:
  CAPSULE  [required]
  QUERY    [required]

Options:
  --limit INTEGER RANGE  [default: 50; 1<=x<=500]
  -h, --help             Show this message and exit.
```

## `reprosec redact`

```text
Usage: reprosec redact [OPTIONS] CAPSULE

  Preview or apply secret redaction to stored request/response records.

Arguments:
  CAPSULE  [required]

Options:
  --apply     Persist redactions after previewing detections.
  -h, --help  Show this message and exit.
```

## `reprosec replay`

```text
Usage: reprosec replay [OPTIONS] CAPSULE REQUEST_ID

  Replay one request through Scope -> Policy -> Rate Limit -> Approval ->
  Executor.

Arguments:
  CAPSULE     [required]
  REQUEST_ID  [required]

Options:
  --allow TEXT                    [required]
  --allow-network TEXT
  --allow-method TEXT             [default: GET, HEAD, OPTIONS]
  --approve-action
  --follow-redirects
  --bind TEXT                     Ephemeral NAME=VALUE secret/variable binding;
                                  never stored in capsule/audit.
  --proxy TEXT                    Explicit proxy URL. Environment proxies are
                                  ignored.
  --approve-proxy-routing         Acknowledge that explicit proxy routing may
                                  control DNS/network destination.
  --max-store-bytes INTEGER       [default: 5000000]
  --max-download-bytes INTEGER    [default: 20000000]
  --debug                         Show full traceback for operational errors.
  --approve-mutation              Deprecated alias for --approve-action.
  -h, --help                      Show this message and exit.
```

## `reprosec report`

```text
Usage: reprosec report [OPTIONS] CAPSULE

  Export a report that separates evidence from hypotheses.

Arguments:
  CAPSULE  [required]

Options:
  --output PATH  [required]
  --format TEXT  [default: md]
  -h, --help     Show this message and exit.
```

## `reprosec research-note`

```text
Usage: reprosec research-note [OPTIONS] CAPSULE

  List or append a reproducible research-notebook entry for the capsule.

Arguments:
  CAPSULE  [required]

Options:
  --text TEXT
  --state TEXT        [default: OBSERVED]
  --evidence-id TEXT
  -h, --help          Show this message and exit.
```

## `reprosec sign`

```text
Usage: reprosec sign [OPTIONS] CAPSULE

  Build the manifest and sign it with a local Ed25519 private key.

Arguments:
  CAPSULE  [required]

Options:
  --private-key PATH  [required]
  -h, --help          Show this message and exit.
```

## `reprosec sync-lineage`

```text
Usage: reprosec sync-lineage [OPTIONS] CAPSULE

  Index RCAP requests/responses/workflow into SRIC lineage and graph stores.

Arguments:
  CAPSULE  [required]

Options:
  -h, --help  Show this message and exit.
```

## `reprosec timeline`

```text
Usage: reprosec timeline [OPTIONS] CAPSULE

  Show a deterministic evidence timeline without inferring missing events.

Arguments:
  CAPSULE  [required]

Options:
  -h, --help  Show this message and exit.
```

## `reprosec update`

```text
Usage: reprosec update [OPTIONS]

  Check or install a signed wheel release; never performs blind git pull.

Options:
  --check
  --manifest-url TEXT
  --public-key PATH
  --current-version TEXT  [default: 0.3.0]
  -h, --help              Show this message and exit.
```

## `reprosec verify`

```text
Usage: reprosec verify [OPTIONS] CAPSULE

  Verify schema-facing manifest hashes and optional signature.

Arguments:
  CAPSULE  [required]

Options:
  --public-key PATH
  -h, --help         Show this message and exit.
```

## `reprosec version`

```text
Usage: reprosec version [OPTIONS]

Options:
  -h, --help  Show this message and exit.
```

## `reprosec web`

```text
Usage: reprosec web [OPTIONS]

  Run the local API. Non-loopback bind is denied in v0.3.

Options:
  --host TEXT     [default: 127.0.0.1]
  --port INTEGER  [default: 8432]
  -h, --help      Show this message and exit.
```

## `reprosec workflow`

```text
Usage: reprosec workflow [OPTIONS] COMMAND [ARGS]...

  Build deterministic multi-actor workflow steps.

Options:
  -h, --help  Show this message and exit.

Commands:
  add  Add a workflow step with explicit actor, dependencies and truth...
```

## `reprosec workflow add`

```text
Usage: reprosec workflow add [OPTIONS] CAPSULE ACTOR REQUEST_ID

  Add a workflow step with explicit actor, dependencies and truth state.

Arguments:
  CAPSULE     [required]
  ACTOR       [required]
  REQUEST_ID  [required]

Options:
  --depends-on TEXT
  --state TEXT       [default: OBSERVED]
  -h, --help         Show this message and exit.
```
