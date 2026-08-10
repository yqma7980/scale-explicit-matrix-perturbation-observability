# G2-20 implementation freeze

Date: 2026-08-10

The following implementation was frozen before generation of the unopened
holdout and before any response-route coverage result was observed.

| File | SHA-256 |
|---|---|
| `implementation/capture_routes.py` | `F7A9F2B8C1AD2A1F43F229142A8334642BA61745AABB4B520D985EE895B48B51` |
| `implementation/compare_precision.py` | `3703BBF92E2EBDD3814406BC71CD21A4FFE54103054F134D76C97E94E553E0AB` |
| `implementation/decimal_backend_audit.py` | `1E826AA06CDC8614DEE32B28BFD167166ED348E980D1E74CDAAE48C1D925BB29` |
| `implementation/evaluate_routes.py` | `5BA141D122ECB8A1E0A314F393B41E87AA1392C7C22CFA64B94A6E6541F1495B` |
| `implementation/generate_holdout.py` | `EE8F2225CB4F72B98660F0EDFF240E186C57F56465044543A6A595DFF101F319` |
| `implementation/run_registered.py` | `C9688F59B09F2682D05655FCD5F5C0C207DD4CD7E6F13840ECB4E428C15CB686` |

`python -m py_compile` passed for all six files before execution.

The independent Decimal backend is an independently implemented arithmetic
route. It is not interval arithmetic, does not use outward rounding, and does
not authorize `certified` or `guaranteed` language.

```text
IMPLEMENTATION_STATUS = FROZEN_NOT_EXECUTED
UNOPENED_HOLDOUT = NOT_GENERATED
```
