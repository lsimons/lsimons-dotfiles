# rsync and nothing else, for bin/claude-docker-sync.sh: it copies the
# session transcripts out of the claude-code-home named volume, which only a
# container can read.
#
# Built by claude-docker/install.py when missing. Rebuild by hand to pick up
# a newer alpine or rsync:
#   docker build -t claude-docker-sync:local ~/git/lsimons/lsimons-dotfiles/claude-docker/sync-image
#
# Pinned to the multi-arch index digest, so the same line builds natively on
# arm64 and amd64. Bump with: docker buildx imagetools inspect alpine:3
FROM alpine:3.24.3@sha256:be2656061b536c1883c4034790e21d0a09c5aaaf51968b89368a3c0371ea2c9a

RUN apk add --no-cache rsync

ENTRYPOINT ["rsync"]
