# Alfred factory commands
export PYTHONPATH := "/Users/akamel/Alfred"

# Capture run fingerprint from live sources
# Usage: just fingerprint [seed=3355]
fingerprint seed="3355":
	python3 scripts/capture_run_fingerprint.py --seed {{seed}}

# Capture run fingerprint with custom tools file
# Usage: just fingerprint-tools tools_file=path/to/tools.json [seed=3355]
fingerprint-tools tools_file seed="3355":
	python3 scripts/capture_run_fingerprint.py --tools-file {{tools_file}} --seed {{seed}}