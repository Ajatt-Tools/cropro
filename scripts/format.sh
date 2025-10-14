#!/bin/bash

set -euo pipefail

readonly ROOT_DIR=$(git rev-parse --show-toplevel)

"$ROOT_DIR/cropro/ajt_common/format.sh"
