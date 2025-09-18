import json
import boto3

dynamodb = boto3.resource('dynamodb')

def lambda_handler(event, context):
    """
    Add or remove tags from images (bulk operation)
    Input: {
        "url": ["thumbnail-url-1", "thumbnail-url-2"],
        "type": 1,  # 1=add, 0=remove
        "tags": ["custom-tag", "event2024"]
    }
    """
    try:
        # Parse request body
        body = json.loads(event.get('body', '{}'))
        urls = body.get('url', [])
        operation_type = body.get('type', 1)  # 1=add, 0=remove
        tags_to_modify = body.get('tags', [])
        
        if not urls or not tags_to_modify:
            return {
                'statusCode': 400,
                'headers': {'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'error': 'urls and tags required'})
            }
        
        # Normalize tags
        tags_to_modify = [tag.strip().lower() for tag in tags_to_modify]
        
        images_table = dynamodb.Table('assignment2-images')
        tag_index_table = dynamodb.Table('assignment2-tag-index')
        
        results = []
        
        for url in urls:
            try:
                # Extract imageId from URL
                image_id = url.split('/thumb/')[1].split('.')[0]
                
                # Get current image data
                response = images_table.get_item(Key={'imageId': image_id})
                if 'Item' not in response:
                    results.append({'url': url, 'status': 'not_found'})
                    continue
                
                current_tags = set(response['Item'].get('tags', []))
                current_tag_counts = response['Item'].get('tagCounts', {})
                
                if operation_type == 1:  # Add tags
                    # Add new tags
                    for tag in tags_to_modify:
                        if tag not in current_tags:
                            current_tags.add(tag)
                            current_tag_counts[tag] = 1
                            
                            # Add to tag index
                            tag_index_table.put_item(
                                Item={
                                    'tag': tag,
                                    'imageId': image_id,
                                    'count': 1
                                }
                            )
                
                else:  # Remove tags (type = 0)
                    # Remove tags
                    for tag in tags_to_modify:
                        if tag in current_tags:
                            current_tags.discard(tag)
                            current_tag_counts.pop(tag, None)
                            
                            # Remove from tag index
                            try:
                                tag_index_table.delete_item(
                                    Key={'tag': tag, 'imageId': image_id}
                                )
                            except:
                                pass  # Tag might not exist in index
                
                # Update main table
                images_table.update_item(
                    Key={'imageId': image_id},
                    UpdateExpression='SET tags = :tags, tagCounts = :counts',
                    ExpressionAttributeValues={
                        ':tags': list(current_tags),
                        ':counts': current_tag_counts
                    }
                )
                
                results.append({
                    'url': url,
                    'status': 'success',
                    'updatedTags': list(current_tags)
                })
                
            except Exception as e:
                results.append({
                    'url': url,
                    'status': 'error',
                    'error': str(e)
                })
        
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Content-Type': 'application/json'
            },
            'body': json.dumps({
                'results': results,
                'operation': 'add' if operation_type == 1 else 'remove'
            })
        }
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': str(e)})
        }