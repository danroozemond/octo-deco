# TODO 
* Check paths in this file

# Installation instructions
* Initialize an sqlite database using `octodeco/flaskr/sql/init-clean.sql`
* check out `config/docker-flask/scripts/*.tmp` and create appropriate copies for yourself

# "Architecture" of octodeco
* `deco`: The library for decompression computations
* `flaskr`: The web interface for decompression insights, including the logic for various charts. 
  Uses flask as primary technology.
  Uses the two HTTP APIs defined below.
* `db`: HTTP API for database operations. Uses FastAPI as technology.
* `user` TODO finish

# Docker
Running in docker is easiest. See `config`, in particular `config/docker-compose`.

# Note on security
There is none.
TODO: Finish