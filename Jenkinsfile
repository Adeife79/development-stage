pipeline {
    agent any 

    environment {
        AWS_ACCESS_KEY_ID = credentials('aws-access-key')
        AWS_SECRET_ACCESS_KEY = credentials('aws-secret-access-key')
        AWS_REGION = 'eu-north-1'
        DOCKER_IMAGE = 'business-app'
        IMAGE_REPOSITORY_NAME = 'business-app-repo'
        IMAGE_TAG = 'latest'
        AWS_ACCOUNT_ID = credentials('aws-account-id')
    }

    stages {
        stage('Checkout') {
            steps {
                git branch: 'main',
                url: "https://github.com/Adeife79/development-stage.git"
            }
        }

        stage ('Create S3 Bucket') {
            environment {
                AWS_REGION = 'eu-north-1'
                BUCKET_NAME = "demo2-terraform-state-bucket"
            }

            steps {
                withCredentials([[
                    $class: 'AmazonWebServicesCredentialsBinding', 
                    credentialsId: 'demo2-aws-credentials'
                ]]) {
                    sh '''
                        aws s3api create-bucket --bucket "$BUCKET_NAME" --region eu-north-1 --create-bucket-configuration LocationConstraint=eu-north-1
                    '''
                }
            }
        }

        stage ('Terraform Init') {
            steps {
                dir('terraform-config') {
                      sh 'terraform init -input=false -backend-config="bucket=${BUCKET_NAME}"'
                }
            }
        }

        stage ('Terraform Plan'){
            steps {
                dir ('terraform-config') {
                    sh 'terraform plan -input=false -out=tfplan'
                }
            }
        }

        stage('Terraform Apply') {
            steps {
                dir ('terraform-config') {
                    sh 'terraform apply -auto-approve tfplan'
                }
            }
        }

        stage ('Build and Push Docker Image to AWS ECR') {  
            steps {
                withCredentials([[
                    $class: 'AmazonWebServicesCredentialsBinding',
                    credentialsId: 'demo2-aws-credentials'
                ]]) {
                    sh """
                        aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com
                        docker build -t $IMAGE_REPOSITORY_NAME:$IMAGE_TAG .
                        docker tag $IMAGE_REPOSITORY_NAME:$IMAGE_TAG $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$IMAGE_REPOSITORY_NAME:$IMAGE_TAG
                        docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$IMAGE_REPOSITORY_NAME:$IMAGE_TAG  
                    """     
                }
                      
            }
        }

        stage ('Run and Deploy Docker Application via SSM') {
            steps {
                script {
                    env.EC2_PUBLIC_IP = sh (
                        script: "cd terraform-config && terraform output -raw ec2_public_ip",
                        returnStdout: true
                    ).trim()
                    env.INSTANCE_ID = sh (
                        script: 'cd terraform-config && terraform output -raw instance_id',
                        returnStdout: true
                    ).trim()
                }

                sh '''
                    aws ec2 wait instance-running --instance-id $INSTANCE_ID --region $AWS_REGION

                    COMMAND_ID=$(aws ssm send-command \
                        --instance-id $INSTANCE_ID \
                        --documnet-name "AWS-RunShellScript" \
                        --parameters 'commands=[
                            "AWS_REPOSITORY_URI=$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$IMAGE_REPOSITORY_NAME",
                            "DOCKER_IMAGE=$DOCKER_IMAGE:$IMAGE_TAG",
                            "sudo systemctl start amazon-ssm-agent || true",
                            "sudo systemctl enable amazon-ssm-agent || true",
                            "sudo dnf update -y >/dev/null 2>&1 || true",
                            "sudo systemctl daemon-reload || true",
                            "sudo dnf install -y docker || true",
                            "sudo systemctl start docker || true",
                            "sudo systemctl enable docker || true",
                            "curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip" ",
                            "unzip awscliv2.zip",
                            "sudo ./aws/install",
                            "aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com",
                            "docker pull $AWS_REPOSITORY_URI:$IMAGE_TAG/$DOCKER_IMAGE:$IMAGE_TAG || docker run -d -p 8085:8085 $AWS_REPOSITORY_URI:$IMAGE_TAG/$DOCKER_IMAGE:$IMAGE_TAG || true"
                        ]' \
                    --region $AWS_REGION \
                    --query "Command.CommandId" \
                    --output text)

            echo "Docker application deployment command sent.Command ID: $COMMAND_ID"
            

            aws ssm wait command-executed \
                --command-id $COMMAND_ID \
                --instance-id $INSTANCE_ID \
                --region $AWS_REGION 
            
            aws ssm get-command-invocation \
                --command-id $COMMAND_ID \
                --instance-id $INSTANCE_ID \
                --region $AWS_REGION 
            '''

            echo "Application successfully deployed!!"
            }
        }
    }
}