# rsync and nothing else, for bin/claude-docker-sync.sh: it copies the
# session transcripts out of the claude-code-home named volume, which only a
# container can read.
#
# Built by claude-docker/install.py when missing. Rebuild by hand to pick up
# a newer alpine or rsync:
#   docker build -t claude-docker-sync:local ~/git/lsimons/lsimons-dotfiles/claude-docker/sync-image
#
# Pinned to the multi-arch index digest, so the same line builds natively on
# arm64 and amd64. Renovate's dockerfile manager bumps tag and digest
# together; to check by hand: docker buildx imagetools inspect alpine:3
FROM alpine:3.24.4@sha256:f59abe656b692d901e184be3445e084786602108599d2a51d229c0f5a48c71bf

RUN apk add --no-cache rsync

ENTRYPOINT ["rsync"]
