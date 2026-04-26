# 📦 Project Setup

---

# 🧩 1. Install Homebrew (Mac Only)

> Skip this step if you're on Windows.

Homebrew is a package manager for macOS.  
You’ll use it to easily install Git, Python, Docker, etc.

**Install Homebrew:**

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

**Verify Homebrew:**

```bash
brew --version
```

If you see a version number, you're good to go.

---

# 🧩 2. Install and Configure Git

## Install Git

- **MacOS (using Homebrew)**

```bash
brew install git
```

- **Windows**

Download and install [Git for Windows](https://git-scm.com/download/win).  
Accept the default options during installation.

**Verify Git:**

```bash
git --version
```

---

## Configure Git Globals

Set your name and email so Git tracks your commits properly:

```bash
git config --global user.name "Your Name"
git config --global user.email "your_email@example.com"
```

Confirm the settings:

```bash
git config --list
```

---

## Generate SSH Keys and Connect to GitHub

> Only do this once per machine.

1. Generate a new SSH key:

```bash
ssh-keygen -t ed25519 -C "your_email@example.com"
```

(Press Enter at all prompts.)

2. Start the SSH agent:

```bash
eval "$(ssh-agent -s)"
```

3. Add the SSH private key to the agent:

```bash
ssh-add ~/.ssh/id_ed25519
```

4. Copy your SSH public key:

- **Mac/Linux:**

```bash
cat ~/.ssh/id_ed25519.pub | pbcopy
```

- **Windows (Git Bash):**

```bash
cat ~/.ssh/id_ed25519.pub | clip
```

5. Add the key to your GitHub account:
   - Go to [GitHub SSH Settings](https://github.com/settings/keys)
   - Click **New SSH Key**, paste the key, save.

6. Test the connection:

```bash
ssh -T git@github.com
```

You should see a success message.

---

# 🧩 3. Clone the Repository

Now you can safely clone the course project:

```bash
git clone <repository-url>
cd <repository-directory>
```

---

# 🛠️ 4. Install Python 3.10+

## Install Python

- **MacOS (Homebrew)**

```bash
brew install python
```

- **Windows**

Download and install [Python for Windows](https://www.python.org/downloads/).  
✅ Make sure you **check the box** `Add Python to PATH` during setup.

**Verify Python:**

```bash
python3 --version
```
or
```bash
python --version
```

---

## Create and Activate a Virtual Environment

(Optional but recommended)

```bash
python3 -m venv venv
source venv/bin/activate   # Mac/Linux
venv\Scripts\activate.bat  # Windows
```

### Install Required Packages

```bash
pip install -r requirements.txt
```

---

# 🐳 5. Docker Setup

## Install Docker

- [Install Docker Desktop for Mac](https://www.docker.com/products/docker-desktop/)
- [Install Docker Desktop for Windows](https://www.docker.com/products/docker-desktop/)

## Run Docker Container

```bash
docker compose up -d
```

---

# 📝 6. Running the Tests

```bash
playwright install
pytest
```

## DockerHub
#### URL: https://hub.docker.com/r/ayushgerra/assignment-repo
![Docker QR Image](/images/QRCode_20260313170037.png "My QR Code Link")


# Calculation Types

The calculator supports ten operation types. Each calculation is saved to your history and can be viewed, edited, or deleted from the dashboard.

---

### Addition
**API type:** `addition`

Sums all provided numbers together. Accepts two or more inputs.

| Inputs | Result |
|--------|--------|
| `5, 10` | `15` |
| `1, 2, 3, 4` | `10` |

---

### Subtraction
**API type:** `subtraction`

Subtracts each number from the one before it, left to right. Accepts two or more inputs.

| Inputs | Result |
|--------|--------|
| `20, 8` | `12` |
| `100, 10, 5` | `85` |

---

### Multiplication
**API type:** `multiplication`

Multiplies all provided numbers together. Accepts two or more inputs.

| Inputs | Result |
|--------|--------|
| `4, 5` | `20` |
| `2, 3, 4` | `24` |

---

### Division
**API type:** `division`

Divides each number by the one that follows it, left to right. Accepts two or more inputs. The divisor cannot be zero.

| Inputs | Result |
|--------|--------|
| `100, 4` | `25` |
| `200, 4, 5` | `10` |

---

### Power
**API type:** `power`

Raises the base to the given exponent. Requires exactly 2 inputs: `[base, exponent]`.

| Inputs | Result |
|--------|--------|
| `2, 10` | `1024` |
| `9, 0.5` | `3` |

---

### Root
**API type:** `root`

Computes the n-th root of a number. Requires exactly 2 inputs: `[number, n]`. The degree cannot be zero.

| Inputs | Result |
|--------|--------|
| `27, 3` | `3` (cube root) |
| `16, 2` | `4` (square root) |

---

### Modulus
**API type:** `modulus`

Returns the remainder after dividing the first number by the second. Requires exactly 2 inputs. The divisor cannot be zero.

| Inputs | Result |
|--------|--------|
| `17, 5` | `2` |
| `10, 3` | `1` |

---

### Integer Division
**API type:** `integer_division`

Divides left to right and discards any remainder, returning a whole number. Accepts two or more inputs. The divisor cannot be zero.

| Inputs | Result |
|--------|--------|
| `17, 3` | `5` |
| `100, 5, 2` | `10` |

---

### Percentage
**API type:** `percentage`

Calculates what percentage the first number is of the second: `(a / b) × 100`. Requires exactly 2 inputs. The second number cannot be zero.

| Inputs | Result |
|--------|--------|
| `25, 200` | `12.5` |
| `1, 4` | `25` |

---

### Absolute Difference
**API type:** `abs_difference`

Returns the positive distance between two numbers, regardless of order. Requires exactly 2 inputs.

| Inputs | Result |
|--------|--------|
| `10, 3` | `7` |
| `3, 10` | `7` |

---

### Input rules summary

| Operation | Min inputs | Max inputs | Zero divisor allowed |
|-----------|-----------|-----------|----------------------|
| Addition | 2 | unlimited | — |
| Subtraction | 2 | unlimited | — |
| Multiplication | 2 | unlimited | — |
| Division | 2 | unlimited | No |
| Power | 2 | 2 | — |
| Root | 2 | 2 | No (degree) |
| Modulus | 2 | 2 | No (divisor) |
| Integer Division | 2 | unlimited | No |
| Percentage | 2 | 2 | No (denominator) |
| Absolute Difference | 2 | 2 | — |