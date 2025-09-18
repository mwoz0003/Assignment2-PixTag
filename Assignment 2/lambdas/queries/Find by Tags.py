import json
import boto3
from boto3.dynamodb.conditions import Key

dynamodb = boto3.resource('dynamodb')

def lambda_handler(event, context):
    """
    Find images by tags with minimum repetition counts
    Query format: ?tags=person,car&counts=2,1
    """
    try:
        # Parse query parameters
        params = event.get('queryStringParameters', {})
        if not params:
            return {
                'statusCode': 400,
                'headers': {'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'error': 'No query parameters provided'})
            }
        
        tags_param = params.get('tags', '').split(',')
        counts_param = params.get('counts', '').split(',')
        
        # Clean and validate input
        tags_with_counts = {}
        for i, tag in enumerate(tags_param):
            tag = tag.strip().lower()
            if tag:
                count = int(counts_param[i]) if i < len(counts_param) else 1
                tags_with_counts[tag] = max(tags_with_counts.get(tag, 0), count)
        
        if not tags_with_counts:
            return {
                'statusCode': 400,
                'headers': {'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'error': 'No valid tags provided'})
            }
        
        # Query the tag index table
        tag_index_table = dynamodb.Table('assignment2-tag-index')
        images_table = dynamodb.Table('assignment2-images')
        
        # Get all images containing each tag
        image_sets = []
        for tag, min_count in tags_with_counts.items():
            response = tag_index_table.query(
                KeyConditionExpression=Key('tag').eq(tag)
            )
            
            # Filter by minimum count
            valid_images = set()
            for item in response['Items']:
                # Note: You'll need to ensure 'count' is stored in the tag-index table
                if item.get('count', 1) >= min_count:
                    valid_images.add(item['imageId'])
            
            image_sets.append(valid_images)
        
        # Find intersection (images with ALL tags)
        if not image_sets:
            matching_images = set()
        else:
            matching_images = image_sets[0]
            for image_set in image_sets[1:]:
                matching_images = matching_images.intersection(image_set)
        
        # Get thumbnail URLs for matching images
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