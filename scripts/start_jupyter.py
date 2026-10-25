"""Start a local authenticated Jupyter server for notebook evidence capture."""
from pathlib import Path
import json
import os
import secrets
import subprocess
import sys

root=Path(__file__).resolve().parents[1]
folder=root/'tmp/jupyter'
folder.mkdir(parents=True,exist_ok=True)
config=folder/'server.json'
config.write_text(json.dumps({
    'IdentityProvider': {'token':secrets.token_urlsafe(32)},
    'ServerApp': {'root_dir':str(root),'open_browser':False,
                  'ip':'127.0.0.1','port':8890,'port_retries':0}
}),encoding='utf-8')
for key,name in [('IPYTHONDIR','ipython'),('JUPYTER_CONFIG_DIR','jupyter'),
                 ('JUPYTER_DATA_DIR','jupyter_data'),('JUPYTER_RUNTIME_DIR','jupyter_runtime')]:
    path=root/'.cache'/name
    path.mkdir(parents=True,exist_ok=True)
    os.environ[key]=str(path)
subprocess.run([sys.executable,'-m','notebook','--config='+str(config)],cwd=root,check=True)
