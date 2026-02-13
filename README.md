# `dmi-reader` — Cross-Platform DMI Hardware Identifier Reader

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.7+](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![PyPI](https://img.shields.io/pypi/v/dmi-reader.svg)](https://pypi.org/project/dmi-reader/)

Securely retrieve unique hardware identifiers (DMI, UUID, serial numbers) across Linux, Windows, and macOS — **without requiring root/admin privileges**.

</div>

---

## 🚀 Features

- ✅ **Cross-Platform**: Works on Linux, Windows, macOS
- ✅ **No Root/Admin Required**: Reads DMI safely without elevated permissions
- ✅ **Thread-Safe Caching**: Efficient, avoids repeated system calls
- ✅ **Container-Aware**: Automatically detects Docker, Podman, etc.
- ✅ **Graceful Degradation**: Handles missing/wrong DMI gracefully
- ✅ **Fallback Support**: Uses `machine-id`, `hostname` when DMI unavailable
- ✅ **Production-Ready**: Robust error handling, logging, type hints

---

## 📦 Installation

```bash
pip install dmi-reader
```

### Dependencies

- On **Windows**: automatically installs `wmi` and `pywin32`
- On **Linux/macOS**: no additional dependencies needed

---

## 💡 Usage

```python
from dmi_reader import get_dmi_info

# Get DMI information
info = get_dmi_info(include_fallback=True)
print(info)
# Example output:
# {'system_uuid': '123e4567-e89b-12d3-a456-426614174000'}

# Or without fallback
info = get_dmi_info(include_fallback=False)
```

---

## 🛠️ Supported Platforms

| Platform | Method | Requires Root/Admin |
|----------|--------|--------------------|
| Linux    | `/sys/class/dmi/id/` | No |
| Windows  | WMI (with timeout) | No |
| macOS    | `system_profiler` | No |

---

## ⚠️ License & Commercial Use

This software is **free for personal and non-commercial use only**.

**Any commercial use** — including but not limited to:
- Integration into commercial products
- Use in business operations
- Distribution as part of paid services
- Use in corporate environments

**requires explicit written permission from the author.**

To request a commercial license, contact:  
**Telegram**: [@saicon001](https://t.me/saicon001)

---

## 🧪 Testing

```bash
# Clone the repository
git clone https://github.com/saiconfirst/dmi-reader.git
cd dmi-reader

# Install dependencies
pip install -r requirements.txt

# Run test script
python test.py
```

---

## 🤝 Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

---

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

<div align="center">

Made with ❤️ by [saiconfirst](https://github.com/saiconfirst)

For commercial licensing inquiries: **[@saicon001](https://t.me/saicon001)**

</div>
