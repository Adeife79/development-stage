pipeline {
    agent any 

    environment {
        AWS_ACCESS_KEY_ID = credentials('aws-access-key')
        AWS_SECRET_ACCESS_KEY = credentials('aws-secret-access-key')
        AWS_REGION = 'eu-north-1'
        DOCKER_IMAGE = 'business-app'
        IMAGE_REPOSITORY_NAME = 'business-app-repo'
        IMAGE_TAG = 'latest'
        AWS_ACCOUNT_ID = '749929394992'
        BUCKET_NAME = "demo2-terraform-state-bucket"
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
                    sh '''
                     rm -rf .terraform
                     rm -f .terraform.lock.hcl
                     rm -f terraform.tfstate
                     rm -f terraform.tfstate.backup
                     terraform init -input=false -reconfigure -backend-config="bucket=${BUCKET_NAME}"
                     '''
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
        
        stage ('Login to ECR'){
            steps {
                withCredentials([aws( credentialsId: 'demo2-aws-credentials')]) {
                     sh '''
                      aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com
                     '''
                }
             }
        }
        
        stage ('Build and Push Docker Image to AWS ECR') {  
            steps {
                dir ('business-app/backend'){
                        sh '''
                            docker build -t $IMAGE_REPOSITORY_NAME .
                            docker tag $IMAGE_REPOSITORY_NAME $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$IMAGE_REPOSITORY_NAME:$IMAGE_TAG
                            docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$IMAGE_REPOSITORY_NAME:$IMAGE_TAG  
                        '''     
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
                    echo "AWS_ACCOUNT_ID=$AWS_ACCOUNT_ID"
                    echo "AWS_REGION=$AWS_REGION"
                    echo "IMAGE_REPOSITORY_NAME=$IMAGE_REPOSITORY_NAME"
                    echo "IMAGE_TAG=$IMAGE_TAG"
                    echo "INSTANCE_ID=$INSTANCE_ID"
                    echo "DOCKER_IMAGE=$DOCKER_IMAGE"
                    
                    aws ec2 wait instance-running --instance-id $INSTANCE_ID --region $AWS_REGION

                    COMMAND_ID=$(aws ssm send-command \
                        --instance-id $INSTANCE_ID \
                        --document-name "AWS-RunShellScript" \
                        --parameters 'commands=[
                            "AWS_REGION=${AWS_REGION}",
                            "AWS_ACCOUNT_ID=${AWS_ACCOUNT_ID}",
                            "IMAGE_REPOSITORY_NAME=$IMAGE_REPOSITORY_NAME",
                            "DOCKER_IMAGE=${DOCKER_IMAGE}",
                            "IMAGE_TAG=$IMAGE_TAG",
                            "sudo systemctl start amazon-ssm-agent || true",
                            "sudo systemctl enable amazon-ssm-agent || true",
                            "sudo dnf update -y >/dev/null 2>&1 || true",
                            "sudo systemctl daemon-reload || true",
                            "sudo dnf install -y docker || true",
                            "sudo systemctl start docker || true",
                            "sudo systemctl enable docker || true",
                            "aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com",
                            "docker pull $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$IMAGE_REPOSITORY_NAME:$IMAGE_TAG || true",
                            "docker stop ${DOCKER_IMAGE} || true",
                            "docker rm ${DOCKER_IMAGE} || true",
                            "docker run -d --name business-app -p 8085:8085 $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$IMAGE_REPOSITORY_NAME:$IMAGE_TAG || true"
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