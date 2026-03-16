terraform { 
    backend "s3" {
        bucket = "demo2-terraform-state-bucket"
        key = "terraform.tfstate"
        region = "eu-north-1"
    }
}


provider "aws" {
    region = "eu-north-1"
}