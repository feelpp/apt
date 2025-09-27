# Feel++ APT Repository

**URL**: https://feelpp.github.io/apt/  
**Public key**: [`feelpp.gpg`](./feelpp.gpg)

## Channels & layout
- Prefixes (channels): `stable/`, `testing/`, `pr/`
- Distributions: `jammy`, `noble` (others possible)
- Components (projects): `feelpp`, `exama`, `hidalgo`, `misc`, …

## Setup (client)
```bash
curl -fsSL https://feelpp.github.io/apt/feelpp.gpg \
  | sudo tee /usr/share/keyrings/feelpp.gpg >/dev/null

# Example: stable + noble, components feelpp and exama
echo "deb [arch=amd64 signed-by=/usr/share/keyrings/feelpp.gpg] \
https://feelpp.github.io/apt/stable noble feelpp exama" \
| sudo tee /etc/apt/sources.list.d/feelpp.list

sudo apt update
