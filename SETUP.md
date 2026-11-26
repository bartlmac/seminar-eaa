# Workshop environment setup: Windows with WSL and Linux

Complete this setup **before the three-hour workshop**. The Windows route uses
Ubuntu in WSL 2; the native Linux route uses Ubuntu or Debian on a Linux desktop.
Both routes then use the same Linux project files, Python 3.11 virtual environment
and VS Code workflow. Other Linux distributions need equivalent system packages.

The project requires **CPython 3.11.x** (`>=3.11,<3.12` in `pyproject.toml`). A
newer system Python does not meet this requirement.

You need internet access for downloads and assistant sign-in, permission to
install system software,
and an account with access to Codex **or** Claude Code. Confirm account access
before the workshop; installing an extension does not provide a subscription.
Use your organisation's approved account and network configuration if applicable.

## 1. Choose your operating-system route

### Windows: install and check WSL 2

Use a Windows version supported by Microsoft's
[WSL installation instructions](https://learn.microsoft.com/en-us/windows/wsl/install).
On a managed computer, arrange installation with IT in advance. Hardware
virtualisation must be enabled if WSL requests it.

Open **Windows Terminal → PowerShell as administrator**. For a new installation:

```powershell
wsl --install -d Ubuntu
```

Restart Windows if prompted. Start Ubuntu and finish the first-run setup,
including a Linux username and password. This password is used by `sudo` and
can differ from your Windows password. Password entry in a Linux terminal shows
no characters; type it and press Enter.

If Ubuntu is already installed, keep the existing installation. In PowerShell,
check its name and WSL version:

```powershell
wsl --update
wsl --list --verbose
```

The Ubuntu entry should show `VERSION 2`. If it shows `1`, convert it:

```powershell
wsl --set-version Ubuntu 2
```

Use the exact distribution name from the list in subsequent commands. For
example, `Ubuntu-24.04` needs `wsl -d Ubuntu-24.04`. For a distribution named
`Ubuntu`, your normal start command is:

```powershell
wsl -d Ubuntu
```

You are now in a Linux shell. Run the remaining `bash` commands there, not in
PowerShell or Command Prompt.

Install **VS Code for Windows** from the
[official download page](https://code.visualstudio.com/download), enabling
**Add to PATH** in the installer. Install Microsoft's **WSL** extension
(`ms-vscode-remote.remote-wsl`) in Windows VS Code. Reopen Windows Terminal
after installation so it picks up the PATH change.

The VS Code desktop window runs on Windows; its server, development tools and
project execution run in Ubuntu through the WSL connection. Installing Linux
desktop VS Code inside WSL is unnecessary for this route. See Microsoft's
[WSL tutorial](https://code.visualstudio.com/docs/remote/wsl-tutorial).

### Native Linux: install VS Code

On a Linux desktop, install the Linux version of VS Code using Microsoft's
[distribution-specific instructions](https://code.visualstudio.com/docs/setup/linux).
For Ubuntu/Debian, download the appropriate `.deb` for your CPU architecture
and install it with the package manager. Open a Linux terminal afterwards.

Continue below. Native Linux does **not** need WSL or a `WSL: Ubuntu` indicator.

## 2. Install Linux utilities and obtain the workshop

In **Ubuntu (WSL or native Linux)**:

```bash
sudo apt update
sudo apt install -y git curl ca-certificates
mkdir -p ~/EAA
```

Place the complete project at `~/EAA/seminar-eaa` by cloning the public
workshop repository; no GitHub account is needed:

```bash
git clone https://github.com/bartlmac/seminar-eaa.git ~/EAA/seminar-eaa
```

The clone includes the hidden directories `.agents` and `.claude`, as well as
sources and tests.

For WSL, keep the working copy in the **Linux filesystem** under `/home/...`,
rather than `/mnt/c/...`, a OneDrive folder or a Windows network share. Create
the virtual environment in Linux; do not copy a Windows virtual environment.

```bash
cd ~/EAA/seminar-eaa
pwd
ls -a
```

You should see `README.md`, `AGENTS.md`, `seminar.json`, `pyproject.toml`, the
three root requirements files, `sources/`, `ontology/`, `tools/` and `tests/`.
Confirm that `sources/Tariff_Calculator.xlsm` is present. Read `README.md` and
`seminar.json` before starting workshop work.

## 3. Open the project in the correct VS Code environment

From the **Linux shell**, in the project root:

```bash
code .
```

On WSL, allow the first connection to install VS Code Server. In the bottom-left
corner, check the remote indicator: it must say **`WSL: Ubuntu`** (or your exact
distribution name). This is the green “flag” in some themes; its colour can
vary. The **text and connection** are what matter. Merely opening an Ubuntu
terminal tab inside an otherwise Windows-local VS Code window is insufficient.

If the indicator is missing, press **Ctrl+Shift+P**, choose
**WSL: Reopen Folder in WSL**, and confirm the Ubuntu distribution. Open the
Linux project folder if necessary.

Choose **Terminal → New Terminal**. On WSL, verify:

```bash
uname -s
echo "$WSL_DISTRO_NAME"
pwd
```

Expected: `Linux`, your Ubuntu distribution name, and a project path under
`/home/...`. On native Linux, `uname -s` also prints `Linux`, while
`WSL_DISTRO_NAME` is normally empty.

Then install the Python extension **in this window**:

1. Open **Extensions** with **Ctrl+Shift+X** and search for `Python`.
2. Select the entry named exactly **Python**, published by **Microsoft**
   (`ms-python.python`). Several similarly named entries appear in the list.
3. On WSL, click **Install in WSL: Ubuntu**. An extension already installed in
   Windows VS Code still needs this step.
4. Check that it is listed under **WSL: Ubuntu – Installed**.

Without this step, the **Python: Select Interpreter** command used in section 5
does not exist. Development extensions must be available in the remote window.
Only trust the workspace after checking that it is the workshop folder you
intended to open.

## 4. Create a Python 3.11 virtual environment

Run these commands in the VS Code **Linux terminal**, from the project root.
Choose **one** of the following methods for a new environment. If `.venv`
already exists, inspect its Python version before reusing it; do not overwrite
an existing environment blindly.

### Method A: Python 3.11 is already available

```bash
python3.11 --version
python3.11 -m venv .venv
```

The version must begin with `Python 3.11.`. If the `venv` module is missing and
your configured Ubuntu repositories provide Python 3.11, install the matching
`python3.11-venv` package. Ubuntu releases ship different default Python versions;
installing `python3` alone does not guarantee 3.11.

If the first command prints `Command 'python3.11' not found`, use Method B. This
is the normal case on Ubuntu 24.04, which ships Python 3.12.

### Method B: obtain Python 3.11 with uv

If Python 3.11 is unavailable, this method installs a user-owned Python without
replacing Ubuntu's system Python. Follow the official
[uv installation instructions](https://docs.astral.sh/uv/getting-started/installation/):

```bash
curl -LsSf https://astral.sh/uv/install.sh -o /tmp/workshop-uv-install.sh
less /tmp/workshop-uv-install.sh
sh /tmp/workshop-uv-install.sh
source "$HOME/.local/bin/env"
```

Press `q` to leave `less`. The last line makes `uv` available in the current
terminal; new terminals find it automatically. If Ubuntu suggests
`sudo snap install astral-uv`, ignore it: that would install a second copy.
Then, from the project root, run:

```bash
uv --version
uv python install 3.11
uv venv --python 3.11 --seed .venv
```

`--seed` supplies pip for the installation commands below. uv is used only to
provide Python and the environment; the workshop still uses its existing
requirements files. See the [uv Python documentation](https://docs.astral.sh/uv/concepts/python-versions/).

### Activate and verify the environment (both methods)

```bash
source .venv/bin/activate
python --version
python -c "import sys; print(sys.executable); assert sys.version_info[:2] == (3, 11); assert sys.prefix != sys.base_prefix"
python -m pip --version
```

The executable and pip location should be inside this project's `.venv`.
The shell prompt commonly shows `(.venv)`. Activation applies only to the current
terminal; a new terminal or assistant shell may need activation again. Explicit
`.venv/bin/python` commands also work without activation. Install project packages
with this interpreter, without `sudo pip` or `--break-system-packages`.

## 5. Install the workshop packages

From the project root, install exactly the provided dependency versions:

```bash
.venv/bin/python -m pip install -r requirements-dev.txt -r requirements-gui.txt
.venv/bin/python -m pip install --no-build-isolation --no-deps .
.venv/bin/python -m pip check
```

| File | Purpose |
|---|---|
| `requirements.txt` | Core workbook export and domain-model dependencies |
| `requirements-dev.txt` | Includes core dependencies, pytest and build tools |
| `requirements-gui.txt` | Includes core dependencies, Streamlit and GUI dependencies |
| `pyproject.toml` | Python 3.11 requirement, workshop package and command metadata |

Both extended requirements files include `requirements.txt`, so the first
command installs all three sets. The second installs the local workshop package
using the build tools already installed. Run it from the directory containing
`pyproject.toml`. The requirements under `calculator/` belong to the application
delivered during the workshop; they do not replace these root setup files.

In VS Code, press **Ctrl+Shift+P → Python: Select Interpreter** and select
`<project>/.venv/bin/python`. If it is absent, choose **Enter interpreter path**
and browse to that file. Open a new terminal and verify the interpreter again.
Editor interpreter selection and terminal activation are separate settings.
See [Python environments in VS Code](https://code.visualstudio.com/docs/python/environments).

## 6. Connect one coding assistant

Install your chosen assistant in the **same project window**. On Windows, first
confirm the `WSL: Ubuntu` indicator. Use its WSL installation option when offered;
verify that commands execute in Linux. The Python requirements do not install
or authenticate these VS Code extensions.

### Option A: Codex

1. Open Extensions and install **Codex** published by **OpenAI**
   (`openai.chatgpt`), using the link in the
   [official OpenAI IDE documentation](https://learn.chatgpt.com/docs/codex/ide).
2. Open the Codex sidebar, or use **Ctrl+Shift+P → Codex: Open Codex Sidebar**.
3. Follow its sign-in flow with the account authorised for your workshop.
   Confirm that you can send a prompt. Account entitlements and organisation
   policies determine access; use the authentication options offered by your
   installation if your organisation uses a different configuration.
4. Use a local session for this folder. Ask Codex to report its working directory,
   Linux environment and `.venv/bin/python` version before doing workshop work.

The WSL connection and Linux path checks follow
[OpenAI's WSL guidance](https://learn.chatgpt.com/docs/windows/wsl).

### Option B: Claude Code

1. Open Extensions and install **Claude Code** published by **Anthropic**
   (`anthropic.claude-code`), following the
   [official Claude Code VS Code instructions](https://code.claude.com/docs/en/vs-code).
2. Open the Claude Code panel via its icon or the **Claude Code** commands in
   **Ctrl+Shift+P**. Sign in through the browser with your approved account.
3. Verify that it can read this project and run `.venv/bin/python` in Linux.

The extension bundles its chat runtime; a separate CLI installation is needed
only if you also want to run `claude` as a terminal command. Use the extension
route for this guide. It does not require adding an assistant Python package
to the workshop environment.

For either assistant, send a preparation prompt such as:

> Read README.md, AGENTS.md and seminar.json. Follow the workshop rules in
> AGENTS.md. Use English. Use .venv/bin/python for Python commands. Report your
> current directory, operating system and Python version. Summarise the workflow
> and available local skills. Do not change files or start a workshop step yet.

Check that it finds the supplied skills under `.agents/skills/` (Codex) or
`.claude/skills/` (Claude Code). Explicitly reference the relevant skill when the
a participant requests a step. Terminal activation in your own tab does not guarantee
activation in the assistant's shell, which is why the prompt specifies the path.

## 7. Verify readiness

From the project root:

```bash
.venv/bin/python -m pip check
.venv/bin/python -m pytest tests/foundation -q
.venv/bin/python -m tools --help
.venv/bin/python -m streamlit version
```

All commands should exit successfully. Foundation tests check the prepared
equipment; they do not establish actuarial correctness. Stop and resolve any
failure before the workshop. Setup ends here: workbook export, extraction,
reference generation, engine implementation and GUI work are separately requested
workshop steps. Participants may request them themselves; in the video seminar,
the tutor calls the next step when everyone is ready. `tools check` and `tools report` require later exercise artifacts.

Excel is unnecessary for exporting the supplied workbook's saved contents.
Creating or changing Excel expectations requires Excel with functioning VBA,
recalculation and saving, as explained in the workshop README.

## 8. Resume work on another day

On Windows, open Windows Terminal and enter `wsl -d Ubuntu`. Then, on either route:

```bash
cd ~/EAA/seminar-eaa
source .venv/bin/activate
code .
```

Check the WSL indicator on Windows and the selected `.venv` interpreter.
The environment persists between sessions; reinstalling packages is normally
needed only after dependency changes or environment recreation. Leave the
environment with `deactivate`.

**After completing the GUI step**, start the application from the
project root:

```bash
.venv/bin/python -m streamlit run calculator/gui/app.py
```

Keep the terminal running and open its local URL, normally
`http://localhost:8501`, in your browser. A Windows browser can normally access
the WSL server through localhost. If automatic browser opening fails, paste
the URL manually. Stop the server with **Ctrl+C**.

## Troubleshooting

| Symptom | Check and remedy |
|---|---|
| WSL cannot start | Check virtualisation, Windows features and restart requirements in Microsoft's WSL guide; involve IT on managed machines. |
| `wsl -d Ubuntu` cannot find the distribution | Run `wsl --list --verbose` in PowerShell and use the exact listed name. |
| `sudo` rejects the Linux password | In PowerShell, not in the Linux shell, run `wsl -d Ubuntu -u root`, then `passwd <your-linux-username>`, set a new password and `exit`. |
| No `Python: Select Interpreter` command | The Python extension is missing in the WSL window. Install it as described in section 3, then run **Developer: Reload Window**. |
| `code: command not found` in WSL | Check Windows VS Code's PATH option and the WSL extension; reopen the terminal. Alternatively connect through VS Code's WSL command and open the Linux folder. |
| No `WSL: Ubuntu` flag | Reopen the folder in WSL. Selecting a WSL terminal alone does not change the workspace connection. |
| Python points to Windows or `/usr/bin/python3` | Select `.venv/bin/python`, activate it in a fresh Linux terminal, or use its explicit path. |
| `python3.11` unavailable | Use Method B; do not substitute a different minor version. |
| `uv: command not found` after installation | Run `source "$HOME/.local/bin/env"` or reopen the terminal; check `~/.local/bin/uv`. |
| `ensurepip`/`venv` missing | Install the matching distro venv package when available, or use the seeded uv method. |
| “externally managed environment” from pip | You are probably installing into system Python. Use `.venv/bin/python -m pip`. |
| A pinned package cannot be found or installed | Verify Python 3.11, CPU architecture, configured package index and network access. Save the exact error for the tutor; do not silently remove pins or change versions. |
| Permission errors in the project | Keep the working copy under your Linux user's home and run VS Code as that user. Avoid creating project files with `sudo`. |
| Assistant cannot authenticate or download | Confirm account access, browser authorisation and proxy/firewall settings. Reload the VS Code window after extension installation if needed. |
| Assistant uses another environment | Confirm its local working folder and ask it to execute the explicit project `.venv/bin/python` path. |
| Streamlit URL does not respond | Keep the server running, check its printed port and errors, and try the exact localhost URL. Have IT check WSL networking if necessary. |

Before the workshop, confirm: the complete project is in Linux; Windows VS Code
shows `WSL: Ubuntu`; Python and pip use `.venv` with Python 3.11; dependencies and
foundation tests pass; and one assistant can read the workshop instructions.
