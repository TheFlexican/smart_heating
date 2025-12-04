# ✅ Development Environment Ready!

Your development environment has been successfully set up!

## What's Installed

✅ Homebrew
✅ Docker Desktop (running)
✅ VS Code with extensions:
   - Remote - Containers
   - Python
   - Pylance
   - Black Formatter
   - GitHub Pull Requests

## Next Steps

### 1. Reopen in DevContainer

VS Code should be open now. To start developing:

1. In VS Code, press `Cmd+Shift+P`
2. Type: **"Remote-Containers: Reopen in Container"**
3. Press Enter
4. Wait 5-10 minutes for the container to build (first time only)

You'll see a notification in the bottom-right showing build progress.

### 2. Start Home Assistant

Once the container is ready, you'll see "Dev Container" in the bottom-left corner.

**Option A: Debug Mode (Recommended)**
- Press `F5` to start Home Assistant with debugging enabled
- Set breakpoints by clicking left of line numbers
- Use Debug Console to inspect variables

**Option B: Using Tasks**
- Press `Cmd+Shift+P`
- Select "Tasks: Run Task"
- Choose "Run Home Assistant"

**Option C: Terminal**
```bash
container start
```

### 3. Access Home Assistant

Open your browser to: **http://localhost:9123**

On first run:
1. Create an admin account
2. Set up your location and preferences
3. Skip MQTT setup (configure later if needed)

### 4. Add Your Integration

1. Go to **Settings** → **Devices & Services**
2. Click **+ ADD INTEGRATION**
3. Search for **"Smart Heating"**
4. Click to add (no configuration needed)
5. Check the sidebar for the "Smart Heating" panel (radiator icon)

### 5. Build the Frontend

In the DevContainer terminal:

```bash
cd custom_components/smart_heating/frontend
npm install
npm run build
```

Or use the VS Code task:
- `Cmd+Shift+P` → "Tasks: Run Task" → "Build Frontend"

Then restart Home Assistant to load the built frontend.

## Development Workflow

### Making Changes

1. **Edit Python files** in `custom_components/smart_heating/`
2. **Restart Home Assistant**:
   - Press `Shift+F5` in debug mode
   - Or run task: "Restart Home Assistant"
   - Or terminal: `container restart`

### Frontend Development

```bash
# Development with hot reload
cd custom_components/smart_heating/frontend
npm run dev
# Access at http://localhost:5173

# Production build
npm run build
```

### Viewing Logs

```bash
# Follow logs
container logs

# View log file
tail -f /config/home-assistant.log

# Filter for your integration
grep smart_heating /config/home-assistant.log
```

### Debugging Tips

1. **Set breakpoints** - Click left of line numbers in Python files
2. **Debug Console** - Execute Python code while paused at breakpoint
3. **Watch variables** - Add expressions to Watch panel
4. **Call Stack** - See the execution path

## Common Commands

| Command | Description |
|---------|-------------|
| `F5` | Start debugging |
| `Shift+F5` | Stop/Restart debugging |
| `F9` | Toggle breakpoint |
| `F10` | Step over |
| `F11` | Step into |
| `container start` | Start Home Assistant |
| `container restart` | Restart Home Assistant |
| `container stop` | Stop Home Assistant |
| `container logs` | View logs |

## Resources

- **DevContainer README**: `.devcontainer/README.md`
- **Developer Guide**: `DEVELOPER.md`
- **Architecture**: `ARCHITECTURE.md`
- **Installation**: `INSTALL.md`

## Troubleshooting

### Container won't start
```bash
# Rebuild container
Cmd+Shift+P → "Remote-Containers: Rebuild Container"
```

### Home Assistant won't start
```bash
# Check config
container check-config

# View detailed logs
container logs
```

### Frontend not loading
```bash
cd custom_components/smart_heating/frontend
npm install
npm run build
# Then restart HA
```

## You're Ready to Develop! 🚀

Happy coding! Your changes to the integration will be automatically picked up after restarting Home Assistant.
