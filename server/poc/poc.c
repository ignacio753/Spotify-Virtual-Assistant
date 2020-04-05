#include<stdio.h>
#include<stdlib.h>
#include<sys/socket.h>
#include<netinet/in.h>
#include<string.h>
#include <arpa/inet.h>
#include <fcntl.h> 
#include <unistd.h>
#include<pthread.h>
#include <capture.h>
#include <syslog.h>
#include <errno.h>
#include <ctype.h>

#define PORT 8888
#define TRUE 1

pthread_mutex_t lock = PTHREAD_MUTEX_INITIALIZER;

void * socketThread(void *arg)
{
  // New Socket for this thread
  int new_socket = *((int *)arg);

  // Read the configuration data from the socket
  // Contract looks like this:
  // fps=25&resolution=350x288
  char config_char_before[30];
  recv(new_socket, config_char_before, 30, 0);

  // Clean the input, clear spaces and any special characters 
  char config_char[30];
  int i = 0, c = 0; 
  for(; i < strlen(config_char_before); i++)
  {
    if (isalnum(config_char_before[i]))
    {
      config_char[c] = config_char_before[i];
      c++;
    }
  }
  // Add termination character
  config_char[c] = '\0';

  // Print the config we get
  syslog(LOG_INFO, "Config is: '%s'", config_char);

  // Strream the video data as long as the socket is open
  while(TRUE)  {
    
    // Stream and frame for the video
    media_stream *     stream;
    media_frame *      frame;
    // Will hold the image data
    void *data;			
    // The size of the data
    unsigned long long size;
      
    // Open stream
    syslog(LOG_INFO, "Capturing stream");    
    stream = capture_open_stream(IMAGE_JPEG, config_char);
    // If the camera cannot capture the stream
    if (stream == NULL) {
      syslog(LOG_INFO, "Error opening stream"); 
      syslog(LOG_INFO, "Exiting Socket '%i'", new_socket);

      capture_frame_free(frame);
      capture_close_stream(stream);
      close(new_socket);

      pthread_exit(NULL);
      return EXIT_FAILURE;
    }

    // Capture frame and data
    frame = capture_get_frame(stream);
    data = capture_frame_data(frame);
    size = capture_frame_size(frame); 

    // Send the size of the data
    if( (unsigned)send(new_socket, &size, sizeof(size),0) == -1)                   
    {   
       // If the size of the data could not be send
       syslog(LOG_INFO, "Error sending size"); 
       printf("Error sending size");
       syslog(LOG_INFO, "'errno' error is: %s", strerror(errno)); 
       syslog(LOG_INFO, "Exiting Socket '%i'", new_socket);
       capture_frame_free(frame);
       capture_close_stream(stream);
       close(new_socket);

       pthread_exit(NULL);
    } else  { 

       syslog(LOG_INFO, "Size of data is: %llu", size);
       // Send the actual data			
       if( (unsigned)send(new_socket, data, size, 0) == -1)                   
       {
         // If the data could not be send
         syslog(LOG_INFO, "Error sending data"); 
         syslog(LOG_INFO, "'errno' error is: %s", strerror(errno)); 
         syslog(LOG_INFO, "Exiting Socket '%i'", new_socket);
         capture_frame_free(frame);
         capture_close_stream(stream);
         close(new_socket);

         pthread_exit(NULL);
	}  else { 
	  syslog(LOG_INFO, "Data sucessfully sent");
	}
    } 
    capture_frame_free(frame);
    capture_close_stream(stream);
	
  }

  // Exit socket
  syslog(LOG_INFO, "Exiting Socket '%i'", new_socket);
  close(new_socket);
  pthread_exit(NULL);

}

// Main Function
int main(){

  int serverSocket, newSocket;
  struct sockaddr_in serverAddr;
  struct sockaddr_storage serverStorage;
  socklen_t addr_size;

  // Create socket. 
  serverSocket = socket(PF_INET, SOCK_STREAM, 0);

  // Socket Configuration settings 
  // Address family, Port number, IP address
  serverAddr.sin_family = AF_INET;
  serverAddr.sin_port = htons(PORT); 
  serverAddr.sin_addr.s_addr = INADDR_ANY;
  // Set all bits of the padding field to 0 
  memset(serverAddr.sin_zero, '\0', sizeof serverAddr.sin_zero);

  // Bind the socket 
  bind(serverSocket, (struct sockaddr *) &serverAddr, sizeof(serverAddr));

  // Listen on the socket 
  if(listen(serverSocket,50)==0){
    syslog(LOG_INFO, "Listening");
  }
  else{
    syslog(LOG_INFO, "Error listening to socket");
  }
  // Keep track of the threads
  pthread_t tid[60];
  int i = 0;
  while(TRUE)
  {
    // Accept connection and create a new socket
    addr_size = sizeof serverStorage;
    newSocket = accept(serverSocket, (struct sockaddr *) &serverStorage, &addr_size);

    // For each new request create a thread
    if( pthread_create(&tid[i], NULL, socketThread, &newSocket) != 0 ) {
      syslog(LOG_INFO, "Failed to create thread");
    }
    if( i >= 50)
    {
      i = 0;

      while(i < 50)
      {
        syslog(LOG_INFO, "Joining Thread");
        pthread_join(tid[i++],NULL);
      }

      i = 0;
    }
  }

  return 0;

}
