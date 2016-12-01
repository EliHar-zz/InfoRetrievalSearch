# Info Retrieval Search

### Accessing your Concordia UNIX drive
 * To SSH into your UNIX drive follow the following link for a [step-by-step tutorial] (https://aits.encs.concordia.ca/helpdesk/oldsite/howto/ssh_tunnel.html)

### Install Docker
[Installation guide](https://docs.docker.com/engine/getstarted/step_one/)</br>
[Docker commands](https://docs.docker.com/engine/reference/commandline/)

### Pull Docker container
<code>docker pull elihar/ubuntu_scrapy</code>

### Run Docker container
<code>docker run -v [local/shared/directory/path]:/root/shared -p 9000:9000 -p 8000:8000 -t -i elihar/ubuntu_scrapy /bin/bash</code>

### Using Crawler

### Tokenize and index the corpus

### Run sentiment Analysis

