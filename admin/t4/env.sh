# Source from any working directory. All tools/cache remain project-local.
T4_ROOT=/path/to/ID
export PATH="$T4_ROOT/runtime/t4/tools/go/bin:$T4_ROOT/runtime/t4/tools/pnpm/node_modules/.bin:$PATH"
export GOPATH="$T4_ROOT/runtime/t4/gopath"
export GOMODCACHE="$T4_ROOT/runtime/t4/gomodcache"
export GOCACHE="$T4_ROOT/runtime/t4/gocache"
export GOTOOLCHAIN=local
export CGO_ENABLED=1
export GOPROXY=https://proxy.golang.org,direct
export GOSUMDB=sum.golang.org
