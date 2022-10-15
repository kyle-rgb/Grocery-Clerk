# puppeteer docker configuration with node-slim based images:
- [Official Workarounds for Containerized Puppeteer Browser](https://www.github.com/puppeteer/blob/main/docs/troubshooting.md)
- [Puppeteer Official Image on Node-slim](https://www.github.com/ebidel/try-puppeteer)
- [Handle Sandbox Bug From Base Puppeteer Image](https://www.stackoverflow.com/questions/62345581/node-js-puppeteer-on-docker-no-usable-sandbox)
- [Bash into Container as Root With Other Users](https://www.github.com/oracle/docker-images/issues/1336)
- [Xvfb Apt Dependencies](https://stackoverflow.com/questions/51667599/issue-in-executing-puppeteer-in-headful-mode-in-docker)

# docker secrets
- [Exporting Env Files from Secrets Definitions](https://stackoverflow.com/questions/48094850/docker-stack-setting-environment-variable-from-secrets)
- [Setting Up Secrets and Swarm](https://earthly.dev/blog/docker-secrets/)

# docker-compose and Dockerfile
- [docker-compose.yaml file reference](https://docs.docker.com/compose/compose-file/)  
- [Dockfile reference](https://docs.docker.com/compose/compose-file/)
- [React Django Template Dockerfiles / docker-compose.yaml](https://github.com/ohduran/cookiecutter-react-django/blob/master/%7B%7Bcookiecutter.project_slug%7D%7D/docker-compose.yml)
- [Docker Node.js Image Specifications](https://github.com/nodejs/docker-node/blob/02a64a08a98a472c6141cd583d2e9fc47bcd9bfd/18/buster-slim/Dockerfile)
- [Cache examples](https://docs.docker.com/build/building/cache/)

# docker security options
- [seccomp options](https://github.com/docker/labs/tree/master/security/seccomp)
- [seccomp man page](https://man7.org/linux/man-pages/man3/seccomp_rule_add.3.html)
-     """    security_opt:
      - seccomp=./scraper/chrome.json"""

# docker puppeteer.js headful helpers
- [puppeteer headful overwrite entrypoint.sh](https://github.com/mujo-code/puppeteer-headful/blob/master/entrypoint.sh)
- [puppeteer headful monitoring with x11vnc + fluxbox](https://stackoverflow.com/questions/12050021/how-to-make-xvfb-display-visible)
- [xvfd start with fluxbox bash script + article](https://medium.com/dot-debug/running-chrome-in-a-docker-container-a55e7f4da4a8)

# Bash Scripting
- [Bash Man Page](https://tiswww.case.edu/php/chet/bash/bashref.html#Special-Parameters)