export DOCKER_BUILDKIT=1

GIT_TAG ?= $(shell git rev-parse --short HEAD)
ifeq ($(GIT_TAG),)
        GIT_TAG=latest
endif

PUBLIC-UTILS_IMG = frameshiftgenomics/mosaic-public-utils:${GIT_TAG}

build-image:
        docker build -t $(PUBLIC-UTILS_IMG) .

push-image:
        docker push $(PUBLIC-UTILS_IMG)
