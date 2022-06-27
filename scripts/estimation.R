if(!require(logistf)){
    install.packages('logistf')
    library(logistf)
}
# install.packages('logistf')
# library(logistf)

setwd('c:/git_repos/impax')
dnoe <- read.table('data/vars_Niederoesterreich.csv', header = TRUE, sep = ',')
# forml <- "zoning ~ lcoe+building_count+settlements+airports+protected_areas+bird_areas+slope+roads"
forml <- "zoning ~ lcoe+settlements+airports+remote_buildings+roads+waters+protected_areas+bird_areas"
ffit <- logistf(forml, dnoe)
# ffitd <- drop1(ffit)
flacfit <- flac(ffit, dnoe)
fpred <- predict(ffit, dnoe, type = 'response')
flacpred <- predict(flacfit, dnoe, type = 'response')
prediction <- data.frame(x=dnoe["x"], y=dnoe["y"], predict=flacpred)
write.csv(prediction, 'data/flac_prediction.csv')