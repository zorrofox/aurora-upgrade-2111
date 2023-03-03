import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import * as rds from 'aws-cdk-lib/aws-rds';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as fs from 'fs';
import * as path from 'path';
import * as assets from 'aws-cdk-lib/aws-s3-assets';

export class AuroraUpgrade2111Stack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    const vpc = new ec2.Vpc(this, 'Aurora DB Testing VPC', {
      ipAddresses: ec2.IpAddresses.cidr('10.0.0.0/16'),
    });
    var clusters = [];
    const versions = [rds.AuroraMysqlEngineVersion.VER_2_10_0,
      rds.AuroraMysqlEngineVersion.VER_2_10_1,
      rds.AuroraMysqlEngineVersion.VER_2_10_2,
      rds.AuroraMysqlEngineVersion.VER_2_10_3,
      rds.AuroraMysqlEngineVersion.VER_2_09_0,
      rds.AuroraMysqlEngineVersion.VER_2_09_1,
      rds.AuroraMysqlEngineVersion.VER_2_09_2,
    ];
    const instanceSg = new ec2.SecurityGroup(this, 'MySQL Client SG', {
      vpc: vpc,
    });
    instanceSg.addIngressRule(ec2.Peer.anyIpv4(), ec2.Port.tcp(22), 'Allow SSH from anywhere');

    const rdsSg = new ec2.SecurityGroup(this, 'Aurora RDS SG', {
      vpc: vpc,
    });
    rdsSg.addIngressRule(ec2.Peer.securityGroupId(instanceSg.securityGroupId), ec2.Port.tcp(3306), 'All Mysql clinet connect');
    for (var v of versions) {
      clusters.push(new rds.DatabaseCluster(this, `${v.auroraMysqlFullVersion.replace('5.7.', '')}`, {
        engine: rds.DatabaseClusterEngine.auroraMysql({ version: v }),
        credentials: rds.Credentials.fromPassword('admin', cdk.SecretValue.unsafePlainText('Welcome#123456')),
        instanceProps: {
          instanceType: ec2.InstanceType.of(ec2.InstanceClass.MEMORY5, ec2.InstanceSize.XLARGE),
          vpcSubnets: {
            subnetType: ec2.SubnetType.PRIVATE_WITH_EGRESS,
          },
          vpc: vpc,
          securityGroups: [rdsSg],
        },
        cloudwatchLogsExports: ['audit', 'error', 'general', 'slowquery'],
      }));
    }

    const scriptAsset = new assets.Asset(this, 'MyScriptAsset', {
      path: path.join(__dirname, '../multi_conn_mysql_v1.0.py'),
    });

    const userData = ec2.UserData.forLinux();
    userData.addCommands('yum update -y', 
    'yum install mysql -y',
    'amazon-linux-extras install epel -y',
    'yum install sysbench -y',
    'yum install python3-devel mysql-devel redhat-rpm-config gcc -y',
    'pip3 install mysqlclient pytz DBUtils==1.3 config_file',
    `sudo aws s3 cp s3://${scriptAsset.s3BucketName}/${scriptAsset.s3ObjectKey} /tmp/multi_conn_mysql_v1.0.py`,
    'sudo chmod +x /tmp/multi_conn_mysql_v1.0.py');

    const role = new iam.Role(this, 'MyEC2Role', {
      assumedBy: new iam.ServicePrincipal('ec2.amazonaws.com'),
    });
    role.addManagedPolicy(iam.ManagedPolicy.fromAwsManagedPolicyName('AmazonSSMManagedInstanceCore'));
    scriptAsset.grantRead(role);

    new ec2.Instance(this, 'MySQL Cliet Instance', {
      vpc: vpc,
      vpcSubnets: {
        subnetType: ec2.SubnetType.PUBLIC,
      },
      role: role,
      machineImage: ec2.MachineImage.latestAmazonLinux({
        generation: ec2.AmazonLinuxGeneration.AMAZON_LINUX_2,
      }),
      instanceType: ec2.InstanceType.of(ec2.InstanceClass.T3, ec2.InstanceSize.MEDIUM),
      userData: userData,
      securityGroup: instanceSg,
    });
  }
}
