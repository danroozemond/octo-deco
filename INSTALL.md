# TODO 
* Check paths in this file

# To use the package only
If you just want the computations and don't need/want the webapp (yet), just go

`$ pip install octodeco`

If there is no binary available for your environment, you will need to have `gcc` and 
the python development libraries eg `libpython3-dev` installed.

# Installation instructions
* Initialize an sqlite database using `octodeco/flaskr/sql/init-clean.sql`
* check out `config/docker-flask/scripts/*.tmp` and create appropriate copies for yourself

# "Architecture" of octodeco
* `deco`: The library for decompression computations
* `flaskr`: The web interface for decompression insights, including the logic for various charts. 
  It also includes the logic for dealing with a collection of dives, belonging to users, that may 
  be added, removed, changed, shared, etc.
  Uses flask as primary technology.
  Uses the two HTTP APIs defined below.
* `db`: HTTP API for database operations. Uses FastAPI as technology.

# Docker
Running in docker is easiest. See `config`, in particular `config/docker-compose`.

# Note on security
There is none.
TODO: Finish