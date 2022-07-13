if(!require(logistf)){
    install.packages('logistf')
    library(logistf)
}
if(!require(vtable)){
    install.packages('vtable')
    library(vtable)
}

setwd('c:/git_repos/impax')
dnoe <- read.table('data/vars_Niederoesterreich_touched.csv', header = TRUE, sep = ',')
dnoe$inhab <- ((dnoe$building_count + dnoe$settlements) > 0) * 1

# forml <- "zoning ~ lcoe + settlements + building_count + airports + protected_areas + bird_areas + roads  + slope + waters"  # statistically preferred
forml <- "zoning ~ 1 + lcoe + generation + inhab + building_count + proximity_buildings + protected_areas + bird_areas + airports + slope"
# forml <- "zoning ~ lcoe + settlements + remote_buildings + airports + protected_areas + bird_areas + roads + slope"
ffit <- logistf(forml, dnoe, control = logistf.control(maxit = 1000))
2*(ffit$df + 1) - 2*ffit$loglik  # AIC
cfit <- logistf("zoning ~ 1", dnoe)
pseudorsq <- 1-ffit$loglik/cfit$loglik


# continuous variables: lcoe - 0.084, d_settlements - 0.004, proximity_buildings - 0.133, building_count - 0.0298,
# d_remote - 0.0193, d_roads - 0.004, d_waters - 0.01, slope - 0.0804, generation - 0.0721
# discrete variables: settlements - 0.0024, airports - 0.0003, protected_areas - 0.0064, bird_areas - 0.002
# tfit <- logistf("zoning ~ 1 + lcoe + generation + inhab + building_count + proximity_buildings + protected_areas + bird_areas + airports + slope", dnoe)  #
# 1-tfit$loglik/cfit$loglik
# 2*(tfit$df + 1) - 2*tfit$loglik

# ffit$coefficients / ffit$coefficients[2]
# ffitd <- drop1(ffit)
flacfit <- flac(ffit, dnoe)
summary(flacfit)
# Probabilities - Lower Austria
prob_state <- predict(flacfit, dnoe, type = 'response')
prob_state <- data.frame(x=dnoe["x"], y=dnoe["y"], probability=prob_state)
write.csv(prob_state, 'data/prob_state.csv')
# Valuation - Lower Austria
val_state <- (predict(flacfit, dnoe, type = 'link') - flacfit$coefficients[1]) / flacfit$coefficients[2] - dnoe$lcoe
externality <- data.frame(x=dnoe["x"], y=dnoe["y"], externality=val_state)
write.csv(externality, 'data/externality_state.csv')


# Austria
daut <- read.table('data/vars_austria_touched.csv', header = TRUE, sep = ',')
daut$inhab <- ((daut$building_count + daut$settlements) > 0) * 1
# Probability - Austria
prob_aut <- predict(flacfit, daut, type = 'response')
prob_aut <- data.frame(x=daut["x"], y=daut["y"], probability=prob_aut)
write.csv(prob_aut, 'data/prob_austria.csv')
# Valuation - Austria
val_aut <- (predict(flacfit, daut, type = 'link') - flacfit$coefficients[1]) / flacfit$coefficients[2] - daut$lcoe
externality_aut <- data.frame(x=daut["x"], y=daut["y"], externality=val_aut)
write.csv(externality_aut, 'data/externality_aut.csv')
# Total Cost - Austria
tcost <- (predict(flacfit, daut, type = 'link') - flacfit$coefficients[1]) / flacfit$coefficients[2]
total_cost <- data.frame(x=daut['x'], y=daut['y'], cost=tcost)
write.csv(total_cost, 'data/total_cost_austria.csv')
