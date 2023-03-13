export DOCKER_BUILDKIT=1

GIT_TAG=latest

PUBLIC-UTILS_IMG = frameshiftgenomics/mosaic-public-utils:${GIT_TAG}

build-image:
	docker build --no-cache --platform amd64 -t $(PUBLIC-UTILS_IMG) .

push-image:
	docker push $(PUBLIC-UTILS_IMG)
