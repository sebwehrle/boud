sets
l        laenge
b        breite
i        abstand in laenge
j        abstand in breite
;

parameter
lcoe(l,b)        levelized cost of electricity
num_turbines     number of turbines to place
;

$gdxin input_data
$load    l b i j lcoe num_turbines
$gdxin

lcoe(l,b)$(lcoe(l,b) < 1) = 9999;

variable
total_cost       total cost
;

binary variable
build(l,b)
;

equations
obj, consum,
quad_1, quad_2, quad_3, quad_4
;

obj..
total_cost =E= sum((l,b), lcoe(l,b) * build(l,b));
consum.. sum((l,b), build(l,b)) =G= num_turbines;
quad_1(l,b,i,j)$((ord(i)>1 OR ord(j)>1) AND (ord(i)<card(i) OR ord(j)<card(j)))..
         build(l+(ord(i)-1), b+(ord(j)-1)) =L= 1 - build(l,b);
quad_2(l,b,i,j)$((ord(i)>1 OR ord(j)>1) AND (ord(i)<card(i) OR ord(j)<card(j)))..
         build(l+(ord(i)-1), b-(ord(j)-1)) =L= 1 - build(l,b);
quad_3(l,b,i,j)$((ord(i)>1 OR ord(j)>1) AND (ord(i)<card(i) OR ord(j)<card(j)))..
         build(l-(ord(i)-1), b-(ord(j)-1)) =L= 1 - build(l,b);
quad_4(l,b,i,j)$((ord(i)>1 OR ord(j)>1) AND (ord(i)<card(i) OR ord(j)<card(j)))..
         build(l-(ord(i)-1), b+(ord(j)-1)) =L= 1 - build(l,b);
* $((ord(i)<card(i)) AND (ord(j)<card(j)))

model siting / all /

* parallel mode on
options
threads = 6,
optCR = 0.01,
BRatio = 1
;

*memoryemphasis 1
$onecho > cplex.opt
lpmethod 4
fraccuts=-1
solvefinal 0
names no
$offecho
siting.OptFile = 1;

solve siting using MIP minimizing total_cost

parameter lcoe_spatial(l,b);
lcoe_spatial(l,b) = lcoe(l,b) * build.L(l,b);
display lcoe_spatial;
