# Core Linux CLI Development Tools Verification Test Report

## Overview
This test report documents the installation, configuration, and functional verification of all **Core Linux CLI development tools** per **Section 7 of `instruction.md`**.

The verified toolchain includes general command-line utilities, structured text processors, search engines, build tools, packaging utilities, and file analyzers:
`git`, `gh`, `curl`, `wget`, `jq`, `yq`, `ripgrep`, `fd-find` (with symlink `fd`), `fzf`, `tree`, `make`, `cmake`, `ninja-build`, `pkg-config`, `zip`, `unzip`, `tar`, `xz-utils`, and `file`.

---

## 1. Toolchain Inventory & Installation Status

| Tool | Package / Binary | Category / Scope | Installed Version | Binary Path | Verification Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **git** | `git` | Distributed Version Control | `2.53.0` | `/usr/local/bin/git` | **PASS** |
| **gh** | `gh` | GitHub Official CLI | `2.88.0` | `/usr/bin/gh` | **PASS** |
| **curl** | `curl` | URL Transfer / HTTP Client | `8.5.0` | `/usr/bin/curl` | **PASS** |
| **wget** | `wget` | Network File Retriever | `1.21.4` | `/usr/bin/wget` | **PASS** |
| **jq** | `jq` | Command-line JSON Processor | `1.7` | `/usr/bin/jq` | **PASS** |
| **yq** | `yq` | YAML / JSON / XML Processor | `v4.53.6` | `/usr/local/bin/yq` | **PASS** |
| **ripgrep** | `ripgrep` (`rg`) | Fast Line-oriented Regex Search | `14.1.0` | `/usr/bin/rg` | **PASS** |
| **fd-find** | `fd-find` (`fdfind`) | Fast User-friendly File Search | `9.0.0` | `/usr/bin/fdfind` | **PASS** |
| **fd** | `fd` (symlink) | Symlinked CLI Alias | `9.0.0` | `/usr/local/bin/fd` | **PASS** |
| **fzf** | `fzf` | Command-line Fuzzy Finder | `0.44.1` | `/usr/bin/fzf` | **PASS** |
| **tree** | `tree` | Recursive Directory Tree Lister | `2.1.1` | `/usr/bin/tree` | **PASS** |
| **make** | `make` | GNU Build Automation Engine | `4.3` | `/usr/bin/make` | **PASS** |
| **cmake** | `cmake` | Cross-Platform Build System Generator | `3.28.3` | `/usr/bin/cmake` | **PASS** |
| **ninja-build**| `ninja-build` (`ninja`)| High-speed Build System | `1.11.1` | `/usr/bin/ninja` | **PASS** |
| **pkg-config** | `pkg-config` | Package Compiler/Linker Flag Helper | `1.8.1` | `/usr/bin/pkg-config` | **PASS** |
| **zip** | `zip` | Deflate Compression Archiver | `3.0` | `/usr/bin/zip` | **PASS** |
| **unzip** | `unzip` | ZIP Extraction Utility | `6.00` | `/usr/bin/unzip` | **PASS** |
| **tar** | `tar` | GNU Tape Archiver (tar/tar.gz) | `1.35` | `/usr/bin/tar` | **PASS** |
| **xz-utils** | `xz-utils` (`xz`) | LZMA2 High-Ratio Compression | `5.8.2` (conda) / `5.4.5` (sys) | `/opt/conda/bin/xz` (`/usr/bin/xz`) | **PASS** |
| **file** | `file` | MIME & File Type Classifier | `5.45` | `/usr/bin/file` | **PASS** |

---

## 2. Symlink Configuration

Per requirement, `fd-find` installs `/usr/bin/fdfind` on Debian/Ubuntu systems. A symlink was created and verified at `/usr/local/bin/fd`:

```bash
sudo ln -sf $(which fdfind) /usr/local/bin/fd
ls -la /usr/local/bin/fd
```
**Verification Output:**
```text
lrwxrwxrwx 1 root root 15 Sep  1 16:57 /usr/local/bin/fd -> /usr/bin/fdfind
```
Both `fd --version` and `fdfind --version` resolve to `fdfind 9.0.0`.

---

## 3. Tool-by-Tool Functional Verification

### 3.1 Version Control & Forge Integration

#### `git`
- **Command**: `git --version`
- **Output**: `git version 2.53.0`
- **Functional Test**: Initialized test repository, committed test file, and inspected `git log`:
  ```text
  [main (root-commit) ee54e3c] initial commit
   1 file changed, 1 insertion(+)
   create mode 100644 file.txt
  ```

#### `gh`
- **Command**: `gh --version`
- **Output**:
  ```text
  gh version 2.88.0 (2026-03-10)
  https://github.com/cli/cli/releases/tag/v2.88.0
  ```

---

### 3.2 Network Retrieval & HTTP Clients

#### `curl`
- **Command**: `curl --version`
- **Output**: `curl 8.5.0 (x86_64-pc-linux-gnu) libcurl/8.5.0 OpenSSL/3.0.13 zlib/1.3 brotli/1.1.0 zstd/1.5.5 libidn2/2.3.7 libpsl/0.21.2 nghttp2/1.59.0`
- **Functional Test**: HTTP POST request with multipart upload to `httpbin.org/post` returned HTTP 200 with JSON echo.

#### `wget`
- **Command**: `wget --version`
- **Output**: `GNU Wget 1.21.4 built on linux-gnu.`
- **Functional Test**: Downloaded HTML payload from remote endpoint to standard output.

---

### 3.3 Structured Data Processors

#### `jq`
- **Command**: `jq --version`
- **Output**: `jq-1.7`
- **Functional Test**: Extracted nested JSON fields:
  ```bash
  echo '{"status": "ok", "agent": "core-cli"}' | jq -r .agent
  # Output: core-cli
  ```

#### `yq`
- **Command**: `yq --version`
- **Output**: `yq (https://github.com/mikefarah/yq/) version v4.53.6`
- **Functional Test**: Parsed and extracted YAML document keys:
  ```bash
  echo -e "agent: core-cli\nversion: 1.0" | yq .agent
  # Output: core-cli
  ```

---

### 3.4 Search, Discovery & Filtering

#### `ripgrep` (`rg`)
- **Command**: `rg --version`
- **Output**: `ripgrep 14.1.0 (features: +pcre2, SIMD: SSE2, SSSE3, AVX2)`
- **Functional Test**: Executed regex pattern search on sample text file (`rg "target_line" rg_test.txt`), correctly matched line 2 with line numbering.

#### `fd-find` & `fd`
- **Command**: `fd --version`
- **Output**: `fdfind 9.0.0`
- **Functional Test**: Traversed nested directory structure to locate target file (`fd "special_marker" .`).

#### `fzf`
- **Command**: `fzf --version`
- **Output**: `0.44.1 (debian)`
- **Functional Test**: Filtered multiline stream using non-interactive filter flag (`echo -e "first\nsecond_match\nthird" | fzf --filter="second"`).

#### `tree`
- **Command**: `tree --version`
- **Output**: `tree v2.1.1`
- **Functional Test**: Rendered ASCII hierarchical tree representation of nested directory tree.

---

### 3.5 Build Systems & Compilation Utilities

#### `make`
- **Command**: `make --version`
- **Output**: `GNU Make 4.3`
- **Functional Test**: Executed target from custom `Makefile`, successfully printed target message.

#### `cmake`
- **Command**: `cmake --version`
- **Output**: `cmake version 3.28.3`
- **Functional Test**: Configured and built custom `CMakeLists.txt` project with Unix Makefiles generator.

#### `ninja-build` (`ninja`)
- **Command**: `ninja --version`
- **Output**: `1.11.1`
- **Functional Test**: Parsed custom `build.ninja` rule and executed build target successfully.

#### `pkg-config`
- **Command**: `pkg-config --version`
- **Output**: `1.8.1`
- **Functional Test**: Queried installed system pkg-config packages (`uuid`, `openssl`, `libcrypto`, `python-3.12-embed`, `libsecret-1`).

---

### 3.6 Compression, Archival & File Identification

#### `zip` & `unzip`
- **Commands**: `zip -v`, `unzip -v`
- **Outputs**: `Zip 3.0 (Info-ZIP)`, `UnZip 6.00 (Info-ZIP)`
- **Functional Test**: Created deflate `.zip` archive, decompressed with `unzip -d`, and verified file integrity.

#### `tar`
- **Command**: `tar --version`
- **Output**: `tar (GNU tar) 1.35`
- **Functional Test**: Created gzip-compressed archive (`tar -czvf`), extracted (`tar -xzvf`), and verified payload.

#### `xz-utils` (`xz`)
- **Command**: `xz --version`
- **Output**: `xz (XZ Utils) 5.8.2` (System: `5.4.5`)
- **Functional Test**: Compressed test payload (`xz -z -k`) and decompressed stream (`xz -d -c`).

#### `file`
- **Command**: `file --version`
- **Output**: `file-5.45`
- **Functional Test**: Identified file MIME types for text, Zip archive, and gzip-compressed tarball.

---

## 4. Summary & Verification Matrix

```text
================================================================================
COMPONENT                   STATUS      VERSION         PATH
--------------------------------------------------------------------------------
git                         PASS        2.53.0          /usr/local/bin/git
gh                          PASS        2.88.0          /usr/bin/gh
curl                        PASS        8.5.0           /usr/bin/curl
wget                        PASS        1.21.4          /usr/bin/wget
jq                          PASS        1.7             /usr/bin/jq
yq                          PASS        v4.53.6         /usr/local/bin/yq
ripgrep (rg)                PASS        14.1.0          /usr/bin/rg
fd-find (fdfind)            PASS        9.0.0           /usr/bin/fdfind
fd (symlink)                PASS        9.0.0           /usr/local/bin/fd
fzf                         PASS        0.44.1          /usr/bin/fzf
tree                        PASS        2.1.1           /usr/bin/tree
make                        PASS        4.3             /usr/bin/make
cmake                       PASS        3.28.3          /usr/bin/cmake
ninja-build (ninja)         PASS        1.11.1          /usr/bin/ninja
pkg-config                  PASS        1.8.1           /usr/bin/pkg-config
zip                         PASS        3.0             /usr/bin/zip
unzip                       PASS        6.00            /usr/bin/unzip
tar                         PASS        1.35            /usr/bin/tar
xz-utils (xz)               PASS        5.8.2 / 5.4.5   /opt/conda/bin/xz
file                        PASS        5.45            /usr/bin/file
================================================================================
```

**Overall Status**: **`VERIFIED WORKING`** (100% of Core Linux CLI tools verified).
