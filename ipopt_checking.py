from pyomo.environ import*
import numpy as np
model = ConcreteModel()
model.r = Param (initialize=5)
model.length = Var(bounds=(0,model.r), initialize= model.r)
model.width = Var(bounds=(0,model.r), initialize= model.r )
model.c1 = Constraint(expr= model.length**2 + model.width**2 == model.r**2 )
# model.objfn = Objective(expr= 2*np.pi*(model.width**2)*model.length,sense=maximize)

model.objfn = Objective(expr= 4*model.length*model.width,sense=maximize)
opt = SolverFactory('ipopt')
# opt['NonConvex']=2
results = opt.solve(model)
results.write()
