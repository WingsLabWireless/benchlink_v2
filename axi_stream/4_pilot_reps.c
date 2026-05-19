#include <stdint.h>
#include <stdio.h>
#include <unistd.h>
#include <string.h>
#include <pthread.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <stdlib.h>

#define ARRAY_SIZE 1536
#define PORT 12345
#define PREPEND_SIZE 0
#define RECV_SIZE ARRAY_SIZE
volatile uint32_t array[ARRAY_SIZE];
pthread_mutex_t array_mutex = PTHREAD_MUTEX_INITIALIZER;

int main() {
    int sockfd;
    struct sockaddr_in servaddr, cliaddr;
    if ((sockfd = socket(AF_INET, SOCK_DGRAM, 0)) < 0) {
        perror("socket creation failed");
        exit(EXIT_FAILURE);
    }
    memset(&servaddr, 0, sizeof(servaddr));
    memset(&cliaddr, 0, sizeof(cliaddr));
    servaddr.sin_family = AF_INET; // IPv4
    servaddr.sin_addr.s_addr = INADDR_ANY;
    servaddr.sin_port = htons(PORT);
    if (bind(sockfd, (const struct sockaddr *)&servaddr, sizeof(servaddr)) < 0) {
        perror("bind failed");
        exit(EXIT_FAILURE);
    }
    uint32_t recvArray[RECV_SIZE];
    socklen_t len = sizeof(cliaddr);

  
    while (1) {
        ssize_t n = recvfrom(sockfd, (uint32_t *)recvArray, sizeof(recvArray), MSG_WAITALL, (struct sockaddr *)&cliaddr, &len);
        if (n == RECV_SIZE * sizeof(uint32_t)) {
            memcpy((void *)(array), recvArray, sizeof(recvArray));
        } else {
            perror("Received incorrect amount of data\n");
            exit(EXIT_FAILURE);
        }
        fwrite((const void *)array, sizeof(uint32_t), ARRAY_SIZE, stdout);
        fflush(stdout);
        usleep(3000); // Sleep for 0.0001 seconds
    }
    close(sockfd);
    return 0;
}
