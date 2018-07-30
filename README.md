# miteD
miteD is a base infrastructure component for X1. It encompasses the base classes for the APIs/middleware and is an expansion of 
the Sanic web server to use asyncio and NATS.

## Use
X1 components pull tagged versions of miteD off the pypi server on nexus. For any changes made in this code base to actually reach X1 
without directory shennanigans (covered in developer section) they need to be pushed using:

1. `python3 setup.py bdist_wheel` (Make sure to change the version in setup.py first)
2.  `twine upload -r local dist/*` (This actually pushes to nexus. Check with IT if you need permissions)
3. Delete the `/build`, `/dist` and `.egg-info` files. (This isn't strictly necessary but is a clean up step.)
4. Ensure the X1 componets using your changes have the appropriate miteD version in their requirements file.

## Development
Since this library is (at the moment) entirely used in X1 and X1 pulls miteD from nexus the development cycle could be 
prohibitively slow. To circumvent this:
 1. Copy the `miteD/miteD` folder into the `/src` folder of your X1 component.
 2. Add `ONBUILD ADD src/miteD miteD` to `x1/base/miteD/Dockerfile` below the other onbuild steps.
 3. Build and deploy your images as you would normally to minikube, making changes to `/src/miteD`.
    (this works since python looks in the local directory before checking site packages.)
 4. Once your happy with the state of miteD copy the `src/miteD` directory back into your `miteD` repo and PR as normal.
 5. Delete miteD in the X1 repo.
 
### Gotchyas
 - Since miteD is async functions need to be added to the event loop as co-routines or be called either before 
 `_loop.run_forever()` or after `_loop.close()`. (and please don't block)
 - While `self._app._create_server()` runs (basically the duration the asyncio event loop) `stdout` out is co-opted by the server.
 Use `logging.basicConfig(level=logging.getLevelName(getenv('LOG_LEVEL', 'INFO')))` with `logging.info("Hey")`
