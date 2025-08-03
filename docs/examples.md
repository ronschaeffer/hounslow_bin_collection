# Hounslow Bin Collection Examples

This document contains usage examples for hounslow_bin_collection.

## Python API Usage

### Basic Usage

```python
import hounslow_bin_collection

# Add your API examples here
```

### Configuration

```python
from hounslow_bin_collection.config import config

# Get configuration values
app_name = config.get('app.name')
debug_mode = config.get('app.debug', False)

# Set configuration values
config.set('app.debug', True)
config.save()
```

### Advanced Usage

```python
# Add more complex examples here
```
