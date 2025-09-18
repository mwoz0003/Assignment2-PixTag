import json
import boto3

dynamodb = boto3.resource('dynamodb')

def lambda_handler(event, context):
    """
    Find full-size image URL from thumbnail URL
    Input: {"thumbnailUrl": "https://assignment2-thumbnails-xxxx.s3.amazonaws.com/thumb/UUID.jpg"}
    """
    try:
        # Parse input
        body = json.loads(event.get('body', '{}'))
        thumbnail_url = body.get('thumbnailUrl')
        
        if not thumbnail_url:
            return {
                'statusCode': 400,
                'headers': {'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'error': 'thumbnailUrl required'})
            }
        
        # Extract imageId from thumbnail URL
        # Format: https://assignment2-thumbnails-xxxx.s3.amazonaws.com/thumb/UUID.jpg
        try:
            image_id = thumbnail_url.split('/thumb/')[1].split('.')[0]
        except:
            return {
                'statusCode': 400,
                'headers': {'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'error': 'Invalid thumbnail URL format'})
            }
        
        # Query DynamoDB
        table = dynamodb.Table('assignment2-images')
        response = table.get_item(Key={'imageId': image_id})
        
        if 'Item' not in response:
            return {
                'statusCode': 404,
                'headers': {'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'error': 'Image not found'})
            }
        
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Content-Type': 'application/json'
            },
            'body': json.dumps({
                'fullImageUrl': response['Item'].get('fullImageUrl', ''),
                'imageId': image_id,
                'tags': response['Item'].get('tags', [])
            })
        }
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': str(e)})
        }