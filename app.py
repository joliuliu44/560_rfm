#!/usr/bin/env python3
import os

import aws_cdk as cdk

from final_proj.final_proj_stack import FinalProjStack


app = cdk.App()
FinalProjStack(app, "FinalProjStack",)

app.synth()
