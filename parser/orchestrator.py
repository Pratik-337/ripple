# orchestrator.py

def run_full_impact(change_request):
    parser_result = run_structural_analysis(change_request)

    try:
        semantic_result = run_semantic_layer(parser_result)
        return merge(parser_result, semantic_result)
    except:
        return parser_result