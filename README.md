# Welcome to Aurora upgrade to 2.11.1 testing 

This CDK template will create following Aurora MySQL clusters:
```typescript
    rds.AuroraMysqlEngineVersion.VER_2_10_0,
    rds.AuroraMysqlEngineVersion.VER_2_10_1,
    rds.AuroraMysqlEngineVersion.VER_2_10_2,
    rds.AuroraMysqlEngineVersion.VER_2_10_3,
    rds.AuroraMysqlEngineVersion.VER_2_09_0,
    rds.AuroraMysqlEngineVersion.VER_2_09_1,
    rds.AuroraMysqlEngineVersion.VER_2_09_2,
```

The `cdk.json` file tells the CDK Toolkit how to execute your app.

## Useful commands

* `npm run build`   compile typescript to js
* `npm run watch`   watch for changes and compile
* `npm run test`    perform the jest unit tests
* `cdk deploy`      deploy this stack to your default AWS account/region
* `cdk diff`        compare deployed stack with current state
* `cdk synth`       emits the synthesized CloudFormation template
