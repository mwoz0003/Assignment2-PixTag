import json
import boto3
import base64
from boto3.dynamodb.conditions import Key

dynamodb = boto3.resource('dynamodb')

def lambda_handler(event, context):
    """
    Find images with similar tags to uploaded image
    Input: Base64 encoded image
    Note: This is simplified - normally would call YOLO Lambda
    """
    try:
        # Parse base64 image from request
        body = json.loads(event.get('body', '{}'))
        image_data = body.get('imageData')
        
        if not image_data:
            return {
                'statusCode': 400,
                'headers': {'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'error': 'imageData required'})
            }
        
        # Decode base64 image
        try:
            image_bytes = base64.b64decode(image_data)
        except:
            return {
                'statusCode': 400,
                'headers': {'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'error': 'Invalid base64 image data'})
            }
        
        # TODO: In production, this would call YOLO Lambda to detect objects
        # For now, we'll simulate with dummy tags
        # You would invoke Charlotte's YOLO Lambda here
        
        # Simulated detected tags (replace with actual YOLO detection)
        detected_tags = ['person', 'car']  # Placeholder
        
        # If you want to call another Lambda (YOLO):
        # lambda_client = boto3.client('lambda')
        # yolo_response = lambda_client.invoke(
        #     FunctionName='assignment2-yolo-detection',
        #     InvocationType='RequestResponse',
        #     Payload=json.dumps({'image': image_data})
        # )
        # yolo_result = json.loads(yolo_response['Payload'].read())
        # detected_tags = yolo_result.get('tags', [])
        
        if not detected_tags:
            return {
                'statusCode': 200,
                'headers': {'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'links': [], 'detectedTags': []})
            }
        
        # Query for images with detected tags
        tag_index_table = dynamodb.Table('assignment2-tag-index')
        images_table = dynamodb.Table('assignment2-images')
        
        # Get images for each tag
        image_sets = []
        for tag in detected_tags:
            response = tag_index_table.query(
                KeyConditionExpression=Key('tag').eq(tag)
            )
            image_ids = set(item['imageId'] for item in response['Items'])
            image_sets.append(image_ids)
        
        # Find intersection (images with ALL detected tags)
        if image_sets:
            matching_images = image_sets[0]
            for image_set in image_sets[1:]:
                matching_images = matching_images.intersection(image_set)
        else:
            matching_images = set()
        
        # Get thumbnail URLs
        thumbnail_urls = []
        for image_id in matching_images:
            response = images_table.get_item(Key={'imageId': image_id})
            if 'Item' in response:
                thumbnail_url = response['Item'].get('thumbnailUrl')
                if thumbnail_url:
                    thumbnail_urls.append(thumbnail_url)
        
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Content-Type': 'application/json'
            },
            'body': json.dumps({
                'links': thumbnail_urls,
                'detectedTags': detected_tags,
                'count': len(thumbnail_urls)
            })
        }
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': str(e)})
        }