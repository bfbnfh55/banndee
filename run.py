import argparse
import tempfile
from pathlib import Path
from scripts.prepare_data import prepare, ROOT
from src.core import Store
from src.server import make_server

if __name__ == '__main__':
    parser=argparse.ArgumentParser(description='BaanDee StockGuard local prototype')
    parser.add_argument('--port',type=int,default=8000)
    parser.add_argument('--demo-session',action='store_true',help='Use a fresh temporary database for rehearsal; discarded on exit')
    args=parser.parse_args()
    if not (ROOT/'data/cleaned/manifest.json').exists(): prepare()
    session=tempfile.TemporaryDirectory(prefix='stockguard-demo-') if args.demo_session else None
    store=Store(db=Path(session.name)/'demo.sqlite3') if session else Store()
    store.session_only=bool(session)
    server=make_server(store,args.port)
    if session: print('REHEARSAL: temporary database; changes discarded when this process exits.',flush=True)
    print(f'BaanDee StockGuard: http://127.0.0.1:{server.server_port}',flush=True)
    print('Ctrl+C to stop. '+('REHEARSAL changes are temporary.' if session else 'Drafts persist in data/runtime/stockguard.sqlite3.'),flush=True)
    try: server.serve_forever()
    except KeyboardInterrupt: pass
    finally:
        server.server_close()
        if session: session.cleanup()
