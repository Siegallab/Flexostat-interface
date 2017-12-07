true_GR <- .4/60

starting_OD <- 1

timepoints <- c(0:1000)

true_OD <- starting_OD*(exp(true_GR*timepoints))

plot(timepoints,true_OD)
plot(timepoints,log(true_OD))

OD_noise <- rnorm(length(timepoints),mean=0,sd=20)

observed_OD <- true_OD+OD_noise

plot(timepoints,observed_OD)
lines(timepoints, true_OD,col='red')

plot(timepoints,log(observed_OD))
lines(timepoints, log(true_OD),col='red')