# To use the package only
If you just want the computations and don't need/want the webapp (yet), just go

`$ pip install octodeco`

If there is no binary available for your environment, you will need to have `gcc` and 
the python development libraries e.g. `libpython3-dev` installed.

# Installation instructions including webapp
* Initialize an sqlite database using `octodeco/db/simple/sql/init-clean.sql`
* check out `config/docker-flask/scripts/*.tmpl` and create appropriate copies for yourself
* See `config/docker-compose/docker-compose.dev.yml` for just flask + db connection
* See `config/docker-compose/docker-compose.yml` that also includes nginx and certbot for exposing over https

# "Architecture" of octodeco
* `deco`: The library for decompression computations
* `flaskr`: The web interface for decompression insights, including the logic for various charts. 
  It also includes the logic for dealing with a collection of dives that may be added, removed, changed, etc.
  Uses Flask as primary technology. Uses `db` below through HTTP.
* `db`: HTTP API for database operations. Uses FastAPI as technology.

# Security
In this library, there really is none.