getwd()
setwd('/Users/davidklein/Programming/Flexostat-interface/')

rod <- read.csv('Data/10-20-17/test_data_rod.csv', header = FALSE, col.names = c('Time','1','2','3','4','5','6','7','8'))
stats <- data.frame(matrix(nrow=0, ncol=4, dimnames=list(NULL, c('Hour','Mean','SD','SE'))))

hour <- 2
last <- tail(rod,1)[1]

while(hour<last) {
  ave <- mean(rod$X1[rod$Time < hour & rod$Time > hour-1])
  sd <- sd(rod$X1[rod$Time < hour & rod$Time > hour-1])
  se <- sd/sqrt(length(rod$X1[rod$Time < hour & rod$Time > hour-1]))
  temp <- data.frame(hour,ave,sd,se)
  names(temp) <- c('Hour','Mean','SD','SE')
  stats <- rbind(stats, temp)
  hour <- hour+1
}


