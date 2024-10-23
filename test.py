res = {'type': 'response.done', 'event_id': 'event_ALOUP6JeKnhTD9kzMMACf', 'response': {'object': 'realtime.response', 'id': 'resp_ALOUMd5QOpPnMtCMocWZu', 'status': 'completed', 'status_details': None, 'output': [{'id': 'item_ALOUMoZ4TzgBcPevhrPEF', 'object': 'realtime.item', 'type': 'message', 'status': 'completed', 'role': 'assistant', 'content': [{'type': 'text', 'text': 'The transcript of the audio is: "Over the brow of the... over the next hill. And I think that goes very deep into human character, and I think it was being manifested in those early adventures of people who left Africa and traveled all around the world, and then settling in different parts of the world. I think a lot of anatomical modern human evolution took place outside Africa as well, not only in Africa. So, I guess the general puzzlement that you\'re filled with is..."'}]}], 'usage': {'total_tokens': 304, 'input_tokens': 204, 'output_tokens': 100, 'input_token_details': {'cached_tokens': 0, 'text_tokens': 12, 'audio_tokens': 192}, 'output_token_details': {'text_tokens': 100, 'audio_tokens': 0}}}}


def extract_transcript(response):
    try:
        # Navigate to the 'content' field where the text or audio transcript is stored
        content_list = response['response']['output'][0]['content']
        for content in content_list:
            # Check for text content with the phrase 'The transcript of the audio is:'
            if 'type' in content:
                if content['type'] == 'audio':
                    if 'transcript' in content:
                        if 'unable to process audio' in content['transcript']:
                            return ''
                        elif ':' in content['transcript']:
                            transcript = content['transcript'].split(':')[1].strip().strip('"')
                            return transcript
                        else:
                            return content['transcript']
                elif content['type'] == 'text':
                    if 'text' in content:
                         if 'unable to process audio' in content['text']:
                            return ''
                         elif ':' in content['text']:
                            transcript = content['text'].split(':')[1].strip().strip('"')
                            return transcript
                         else:
                            return content['text']
        return ''
    except KeyError:
        return ''


print(extract_transcript(res))


print(extract_transcript({'type': 'response.done', 'event_id': 'event_ALOUQikKHQo3GxNtKyqX7', 'response': {'object': 'realtime.response', 'id': 'resp_ALOUQw0UHMl3ebcio96hg', 'status': 'completed', 'status_details': None, 'output': [{'id': 'item_ALOUQJtSeq8e1wOdHNzDs', 'object': 'realtime.item', 'type': 'message', 'status': 'completed', 'role': 'assistant', 'content': [{'type': 'text', 'text': '...given at these creatures...'}]}], 'usage': {'total_tokens': 341, 'input_tokens': 333, 'output_tokens': 8, 'input_token_details': {'cached_tokens': 0, 'text_tokens': 122, 'audio_tokens': 211}, 'output_token_details': {'text_tokens': 8, 'audio_tokens': 0}}}}))


print(extract_transcript({'type': 'response.done', 'event_id': 'event_ALOUVvqhUetLdw9K8Sowr', 'response': {'object': 'realtime.response', 'id': 'resp_ALOUUp7zjVXxhf90gLbRI', 'status': 'completed', 'status_details': None, 'output': [{'id': 'item_ALOUUZzAof9LSHTZe5JG6', 'object': 'realtime.item', 'type': 'message', 'status': 'completed', 'role': 'assistant', 'content': [{'type': 'text', 'text': '...explore and spread and try out different environments, why did it take...'}]}], 'usage': {'total_tokens': 413, 'input_tokens': 395, 'output_tokens': 18, 'input_token_details': {'cached_tokens': 0, 'text_tokens': 140, 'audio_tokens': 255}, 'output_token_details': {'text_tokens': 18, 'audio_tokens': 0}}}}))


print(extract_transcript({'type': 'response.done', 'event_id': 'event_ALOUbp62Yr5y9OymkkW3u', 'response': {'object': 'realtime.response', 'id': 'resp_ALOUbXqlghz6uIJwuNpx7', 'status': 'completed', 'status_details': None, 'output': [{'id': 'item_ALOUb8Art1KvCIU3dUyw0', 'object': 'realtime.item', 'type': 'message', 'status': 'completed', 'role': 'assistant', 'content': [{'type': 'text', 'text': "...hundreds of thousands of years for them to develop sophisticated societies and settlements? That's the first big question. Why did it take..."}]}], 'usage': {'total_tokens': 542, 'input_tokens': 513, 'output_tokens': 29, 'input_token_details': {'cached_tokens': 0, 'text_tokens': 216, 'audio_tokens': 297}, 'output_token_details': {'text_tokens': 29, 'audio_tokens': 0}}}}))

print(extract_transcript( {'type': 'response.done', 'event_id': 'event_ALP0gbfbTwGOPip2tBVa5', 'response': {'object': 'realtime.response', 'id': 'resp_ALP0f2uTcChuMSjpQKDGA', 'status': 'incomplete', 'status_details': {'type': 'incomplete', 'reason': 'content_filter'}, 'output': [{'id': 'item_ALP0fJhbGDYp2jBdASrtF', 'object': 'realtime.item', 'type': 'message', 'status': 'incomplete', 'role': 'assistant', 'content': [{'type': 'audio', 'transcript': 'Lifting up of lands that previously had been above water, and I think'}]}], 'usage': {'total_tokens': 300, 'input_tokens': 207, 'output_tokens': 93, 'input_token_details': {'cached_tokens': 0, 'text_tokens': 12, 'audio_tokens': 195}, 'output_token_details': {'text_tokens': 25, 'audio_tokens': 68}}}}))

print(extract_transcript( {'type': 'response.done', 'event_id': 'event_ALP0gbfbTwGOPip2tBVa5', 'response': {'object': 'realtime.response', 'id': 'resp_ALP0f2uTcChuMSjpQKDGA', 'status': 'incomplete', 'status_details': {'type': 'incomplete', 'reason': 'content_filter'}, 'output': [{'id': 'item_ALP0fJhbGDYp2jBdASrtF', 'object': 'realtime.item', 'type': 'message', 'status': 'incomplete', 'role': 'assistant', 'content': [{'type': 'audio', 'transcript': 'The transcript of the audio is: "Lifting up of lands that previously had been above water, and I think"'}]}], 'usage': {'total_tokens': 300, 'input_tokens': 207, 'output_tokens': 93, 'input_token_details': {'cached_tokens': 0, 'text_tokens': 12, 'audio_tokens': 195}, 'output_token_details': {'text_tokens': 25, 'audio_tokens': 68}}}}))

print(extract_transcript({'type': 'response.done', 'event_id': 'event_ALQGewqZm0SeXvLP9CoQ5', 'response': {'object': 'realtime.response', 'id': 'resp_ALQGcYWwzMPX1msf9VGOC', 'status': 'incomplete', 'status_details': {'type': 'incomplete', 'reason': 'content_filter'}, 'output': [{'id': 'item_ALQGcfvN1GLjFB2wja2mO', 'object': 'realtime.item', 'type': 'message', 'status': 'incomplete', 'role': 'assistant', 'content': [{'type': 'audio', 'transcript': "I'm sorry, I'm unable to process audio files. Is there anything else I can help you with?"}]}], 'usage': {'total_tokens': 384, 'input_tokens': 282, 'output_tokens': 102, 'input_token_details': {'cached_tokens': 0, 'text_tokens': 12, 'audio_tokens': 270}, 'output_token_details': {'text_tokens': 31, 'audio_tokens': 71}}}}))


# def extract_titles(response):
#     try:
#         # Navigate to the 'content' field where the text is stored
#         content_list = response['response']['output'][0]['content']
#         for content in content_list:
#             if 'text' in content:
#                 text = content['text']
                
#                 # Check if there's a colon to split by
#                 if ':' in text:
#                     # Split by the colon, get the part after the colon
#                     _, titles_part = text.split(':', 1)
#                 else:
#                     # If no colon, use the whole text
#                     titles_part = text
                
#                 # Split the titles part by newline and filter out any empty strings
#                 titles = [title.strip() for title in titles_part.split('\n') if title.strip()]
#                 return titles
#         return []
#     except KeyError:
#         return []
    

# print(extract_titles({'type': 'response.done', 'event_id': 'event_ALOUWIbGfX8KydBywPxRS', 'response': {'object': 'realtime.response', 'id': 'resp_ALOUVhRa5BktyfvdWgzJd', 'status': 'completed', 'status_details': None, 'output': [{'id': 'item_ALOUVLoRYkuHUs26ksZDB', 'object': 'realtime.item', 'type': 'message', 'status': 'completed', 'role': 'assistant', 'content': [{'type': 'text', 'text': 'The main titles or ideas that can be derived from the discussion so far in the conversation are:\n\n- Human Curiosity and Exploration\n- Early Human Migration Patterns\n- Human Evolution Beyond Africa\n- Anatomical Modern Human Development'}]}], 'usage': {'total_tokens': 515, 'input_tokens': 469, 'output_tokens': 46, 'input_token_details': {'cached_tokens': 0, 'text_tokens': 214, 'audio_tokens': 255}, 'output_token_details': {'text_tokens': 46, 'audio_tokens': 0}}}}))