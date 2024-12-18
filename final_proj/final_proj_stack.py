from aws_cdk import (
    Stack,
    aws_iot as iot,
    aws_lambda as _lambda,
    aws_s3 as s3,
    aws_sqs as sqs,
    aws_events as events,
    aws_lambda_event_sources as lambda_event_sources,
    aws_events_targets as targets,
    aws_iam as iam,
    Duration,
    #imports for aws sns below
    aws_sns as sns,
    aws_sns_subscriptions as subscriptions,
    #core
)
from aws_cdk.aws_lambda_event_sources import S3EventSource
from constructs import Construct



class FinalProjStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        iot_topic = "form_monitor/sensor_data"

        ### SNS topic
        sns_topic = sns.Topic(self, "UserNotificationsTopic", display_name="User Notifications Topic") 
        sns_topic.add_subscription(subscriptions.EmailSubscription("<insert email address>"))
        #sns_topic.add_subscription(subscriptions.SmsSubscription(""))
        ###

        # S3 Buckets for input and output data
        input_bucket = s3.Bucket(self, "InputDataBucket")
        output_bucket = s3.Bucket(self, "OutputDataBucket")

        # Preprocessing Lambda Function
        preprocess_lambda = _lambda.Function(
            self,
            "PreprocessLambda",
            runtime=_lambda.Runtime.PYTHON_3_8,
            handler="preprocess.lambda_handler",
            code=_lambda.Code.from_asset("lambda"),
            environment={
                "INPUT_BUCKET_NAME": input_bucket.bucket_name,
                "OUTPUT_BUCKET_NAME": output_bucket.bucket_name
            }
        )

        # Grant write permissions for preprocess lambda to the input bucket
        input_bucket.grant_read_write(preprocess_lambda)

        # IoT Rule to trigger preprocessing Lambda
        iot_rule = iot.CfnTopicRule(
            self,
            "IoTRule",
            topic_rule_payload={
                "ruleDisabled": False,
                "sql": f"SELECT * FROM '{iot_topic}/#'",
                "actions": [{
                    "lambda": {
                        "functionArn": preprocess_lambda.function_arn
                    }
                }]
            }
        )

        # Allow IoT Core to invoke the preprocessing Lambda function
        preprocess_lambda.add_permission(
            "AllowIotInvoke",
            principal=iam.ServicePrincipal("iot.amazonaws.com"),
            source_arn=iot_rule.attr_arn
        )

        # Train Model Lambda Function
        train_model_lambda = _lambda.Function(
            self,
            "TrainModelLambda",
            runtime=_lambda.Runtime.PYTHON_3_8,
            handler="train_model.train_handler",
            code=_lambda.Code.from_asset("lambda"),
            environment={
                "INPUT_BUCKET_NAME": input_bucket.bucket_name,
            }
        )

        # grant train_model lambda to access s3 bucket
        train_model_lambda.add_to_role_policy(iam.PolicyStatement(
            actions=[
                "s3:PutObject",
                "s3:GetObject"
                ],
            resources=[f"arn:aws:s3:::{input_bucket.bucket_name}/*"]
            ))

        # Grant access to the input bucket for the train_model lambda
        input_bucket.grant_read_write(train_model_lambda)

        # Add S3 event source to trigger TrainModelLambda for "train" directory
        train_model_lambda.add_event_source(S3EventSource(
            input_bucket,
            events=[s3.EventType.OBJECT_CREATED],
            filters=[{
                "prefix": "train/"
            }]
        ))

        # Batch Processing Lambda Function
        batch_processing_lambda = _lambda.Function(
            self,
            "BatchProcessingLambda",
            runtime=_lambda.Runtime.PYTHON_3_8,
            handler="batch_processor.lambda_handler",
            code=_lambda.Code.from_asset("lambda"),
            environment={
                "INPUT_BUCKET_NAME": input_bucket.bucket_name,
                "STATS_FILE_PATH": "train/summary.json",
                "ANOMALY_COUNTS_PATH": "train/anomaly_counts.json"
            }
        )

        # Grant permissions for Batch Processing Lambda to read the input bucket
        input_bucket.grant_read(batch_processing_lambda)
        input_bucket.grant_write(batch_processing_lambda)

        ### Grant permissions for lambda to publish for SNS
        sns_topic.grant_publish(batch_processing_lambda)

        # also add sns topic arn to batch processing lambda environment
        batch_processing_lambda.add_environment("SNS_TOPIC_ARN", sns_topic.topic_arn)
        ###

        # Add S3 event source to trigger BatchProcessingLambda for "demo" directory
        batch_processing_lambda.add_event_source(S3EventSource(
            input_bucket,
            events=[s3.EventType.OBJECT_CREATED],
            filters=[{
                "prefix": "demo/"
            }]
        ))

        # SQS Queue for batch processing (optional, in case of queued workflows)
        batch_queue = sqs.Queue(
            self,
            "BatchQueue",
            visibility_timeout=Duration.seconds(30),
        )

        # Add SQS event source to BatchProcessingLambda if needed
        batch_processing_lambda.add_event_source(lambda_event_sources.SqsEventSource(
            batch_queue,
            batch_size=30,
            max_batching_window=Duration.seconds(10)
            ))

        # EventBridge rule to trigger batch processing Lambda on a schedule (optional)
        rule = events.Rule(
            self,
            "BatchProcessingRule",
            schedule=events.Schedule.rate(Duration.minutes(5)),
        )
        rule.add_target(targets.LambdaFunction(batch_processing_lambda))

