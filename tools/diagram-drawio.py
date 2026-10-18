#!/usr/bin/env python3
"""Generate the shared AWS reference-style diagrams.net architecture diagram."""

from __future__ import annotations

import json
from pathlib import Path
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parent.parent
GRAPH_PATH = ROOT / "docs" / "architecture.tvg.json"
OUTPUT_PATH = ROOT / "docs" / "architecture-aws.drawio"

ACCOUNTS = {
    "aws_account.l3_existing": ("L3アカウント（既存）", 180, 145, 1340, 700, "#8A2BE2"),
    "aws_account.management": ("管理システム用アカウント", 1560, 145, 760, 700, "#147EBA"),
}

# account, icon, label, x, y, AWS category color
NODES = {
    "tv_aws_internet.formrun": (None, None, "formrun\n申請・証跡", 10, 330, "#232F3E"),
    "tv_aws_users.reviewers": (None, None, "審査担当者", 1840, 920, "#232F3E"),
    "aws_apigatewayv2_api.l3_webhook": ("aws_account.l3_existing", "api_gateway", "Amazon API Gateway\nWebhook受付", 80, 180, "#8C4FFF"),
    "aws_lambda_function.l3_ingest": ("aws_account.l3_existing", "lambda", "AWS Lambda\n申請・証跡取込", 260, 180, "#FF9900"),
    "aws_s3_bucket.l3_customer_evidence": ("aws_account.l3_existing", "s3", "Amazon S3\n顧客情報・証跡", 470, 180, "#3F8624"),
    "aws_sfn_state_machine.l3_review": ("aws_account.l3_existing", "step_functions", "AWS Step Functions\n精査ワークフロー", 680, 180, "#E7157B"),
    "tv_aws_textract.ocr": ("aws_account.l3_existing", "textract", "Amazon Textract\n証跡抽出", 870, 180, "#DD344C"),
    "aws_lambda_function.l3_identity": ("aws_account.l3_existing", "lambda", "AWS Lambda\n本人確認", 1060, 180, "#FF9900"),
    "aws_lambda_function.l3_award": ("aws_account.l3_existing", "lambda", "AWS Lambda\n付与判定", 870, 430, "#FF9900"),
    "tv_aws_bedrock.judgement": ("aws_account.l3_existing", "bedrock", "Amazon Bedrock\n判定支援", 1060, 430, "#01A88D"),
    "aws_lambda_function.l3_export_gate": ("aws_account.l3_existing", "lambda", "AWS Lambda\n持出制御", 1210, 180, "#FF9900"),
    "aws_cloudwatch_event_bus.results": ("aws_account.management", "eventbridge", "Amazon EventBridge\n結果イベント", 70, 180, "#E7157B"),
    "aws_sqs_queue.intake": ("aws_account.management", "sqs", "Amazon SQS\n取込キュー", 245, 180, "#E7157B"),
    "aws_sqs_queue.intake_dlq": ("aws_account.management", "sqs", "Amazon SQS\nDLQ", 245, 350, "#E7157B"),
    "aws_lambda_function.receiver": ("aws_account.management", "lambda", "AWS Lambda\n受信・版管理", 420, 180, "#FF9900"),
    "aws_dynamodb_table.applications": ("aws_account.management", "dynamodb", "Amazon DynamoDB\n申請・版履歴", 595, 180, "#527FFF"),
    "aws_apigatewayv2_api.management": ("aws_account.management", "api_gateway", "Amazon API Gateway\n管理API", 420, 350, "#8C4FFF"),
    "aws_cloudfront_distribution.admin": ("aws_account.management", "cloudfront", "Amazon CloudFront\n管理画面", 70, 545, "#8C4FFF"),
    "aws_s3_bucket.admin_web": ("aws_account.management", "s3", "Amazon S3\n静的ファイル", 245, 545, "#3F8624"),
    "aws_cognito_user_pool.staff": ("aws_account.management", "cognito", "Amazon Cognito\n社内認証", 420, 545, "#DD344C"),
}

GROUPS = {
    "group-l3-ingress": ("aws_account.l3_existing", "受付", 35, 105, 390, 280),
    "group-l3-data": ("aws_account.l3_existing", "顧客データ保管", 450, 105, 180, 280),
    "group-l3-review": ("aws_account.l3_existing", "本人確認・付与判定ワークフロー", 655, 105, 535, 520),
    "group-l3-egress": ("aws_account.l3_existing", "アカウント外連携", 1195, 105, 130, 520),
    "group-mgmt-intake": ("aws_account.management", "結果取込", 35, 105, 690, 390),
    "group-mgmt-ui": ("aws_account.management", "管理画面", 35, 500, 520, 175),
}

EDGE_LABELS = {
    ("tv_aws_internet.formrun", "aws_apigatewayv2_api.l3_webhook"): "Webhook",
    ("aws_lambda_function.l3_ingest", "aws_s3_bucket.l3_customer_evidence"): "原本を保存",
    ("aws_s3_bucket.l3_customer_evidence", "tv_aws_textract.ocr"): "原本を参照",
    ("aws_lambda_function.l3_export_gate", "aws_cloudwatch_event_bus.results"): "許可項目のみ",
    ("aws_sqs_queue.intake", "aws_sqs_queue.intake_dlq"): "失敗",
}

STEP_BADGES = {
    "aws_apigatewayv2_api.l3_webhook": ("1", 64, 165),
    "aws_lambda_function.l3_ingest": ("2", 244, 165),
    "aws_sfn_state_machine.l3_review": ("3", 664, 165),
    "tv_aws_textract.ocr": ("4", 854, 165),
    "aws_lambda_function.l3_identity": ("5", 1044, 165),
    "aws_lambda_function.l3_export_gate": ("6", 1194, 165),
    "aws_cloudwatch_event_bus.results": ("7", 54, 165),
    "aws_lambda_function.receiver": ("8", 404, 165),
}

WAYPOINTS = {
    ("aws_lambda_function.l3_ingest", "aws_sfn_state_machine.l3_review"): [(530, 450), (860, 450)],
    ("aws_s3_bucket.l3_customer_evidence", "tv_aws_textract.ocr"): [(740, 500), (1050, 500)],
    ("tv_aws_textract.ocr", "aws_lambda_function.l3_award"): [(1091, 500), (1091, 575)],
    ("aws_lambda_function.l3_award", "aws_lambda_function.l3_export_gate"): [(1091, 690), (1391, 690)],
}


def cell(root: ET.Element, **attributes: str) -> ET.Element:
    return ET.SubElement(root, "mxCell", attributes)


def geometry(parent: ET.Element, x: int, y: int, width: int, height: int) -> None:
    ET.SubElement(parent, "mxGeometry", {
        "x": str(x), "y": str(y), "width": str(width), "height": str(height), "as": "geometry",
    })


def add_text(root: ET.Element, identifier: str, value: str, x: int, y: int,
             width: int, height: int, size: int = 16, bold: bool = False,
             color: str = "#232F3E", align: str = "left") -> None:
    item = cell(root, id=identifier, value=value, vertex="1", parent="1",
                style=("text;html=0;whiteSpace=wrap;verticalAlign=middle;"
                       f"align={align};fontFamily=Arial;fontSize={size};"
                       f"fontStyle={1 if bold else 0};fontColor={color};"
                       "strokeColor=none;fillColor=none;"))
    geometry(item, x, y, width, height)


def add_cloud(root: ET.Element) -> None:
    item = cell(root, id="aws-cloud", value="AWS Cloud", vertex="1", parent="1",
                style=("swimlane;container=1;collapsible=0;recursiveResize=0;startSize=42;"
                       "horizontal=1;rounded=0;html=0;fillColor=#FFFFFF;"
                       "swimlaneFillColor=#FFFFFF;strokeColor=#879196;strokeWidth=2;"
                       "fontFamily=Arial;fontSize=18;fontStyle=1;fontColor=#232F3E;"
                       "align=left;spacingLeft=18;verticalAlign=top;spacingTop=8;"))
    geometry(item, 145, 80, 2220, 805)


def add_account(root: ET.Element, identifier: str, spec: tuple) -> None:
    label, x, y, width, height, stroke = spec
    item = cell(root, id=identifier, value=f"AWS Account  |  {label}", vertex="1", parent="1",
                style=("swimlane;container=1;collapsible=0;recursiveResize=0;startSize=46;"
                       "horizontal=1;rounded=0;html=0;fillColor=#FFFFFF;"
                       f"swimlaneFillColor=#FFFFFF;strokeColor={stroke};strokeWidth=2;"
                       "fontFamily=Arial;fontSize=18;fontStyle=1;fontColor=#232F3E;"
                       "align=left;spacingLeft=16;verticalAlign=top;spacingTop=9;"))
    geometry(item, x, y, width, height)


def add_group(root: ET.Element, identifier: str, spec: tuple) -> None:
    account, label, x, y, width, height = spec
    item = cell(root, id=identifier, value=label, vertex="1", parent=account,
                style=("swimlane;container=0;collapsible=0;startSize=34;horizontal=1;"
                       "rounded=0;html=0;fillColor=#FAFAFA;swimlaneFillColor=#FAFAFA;"
                       "strokeColor=#AAB7B8;strokeWidth=1;dashed=1;dashPattern=6 4;"
                       "fontFamily=Arial;fontSize=14;fontStyle=1;fontColor=#545B64;"
                       "align=left;spacingLeft=12;verticalAlign=top;spacingTop=7;"))
    geometry(item, x, y, width, height)


def add_node(root: ET.Element, identifier: str, spec: tuple) -> None:
    account, icon, label, x, y, color = spec
    if account is None:
        item = cell(root, id=identifier, value=label, vertex="1", parent="1",
                    style=("rounded=0;whiteSpace=wrap;html=0;align=center;verticalAlign=middle;"
                           "fontFamily=Arial;fontSize=16;fontStyle=1;fontColor=#232F3E;"
                           "fillColor=#FFFFFF;strokeColor=#879196;strokeWidth=1;"))
        geometry(item, x, y, 140, 76)
        return
    item = cell(root, id=identifier, value=label, vertex="1", parent=account,
                style=("sketch=0;outlineConnect=0;gradientColor=none;"
                       f"fillColor={color};strokeColor=#FFFFFF;shape=mxgraph.aws4.resourceIcon;"
                       f"resIcon=mxgraph.aws4.{icon};aspect=fixed;html=0;whiteSpace=wrap;"
                       "verticalLabelPosition=bottom;verticalAlign=top;align=center;"
                       "fontFamily=Arial;fontSize=14;fontColor=#232F3E;"
                       "labelBackgroundColor=#FFFFFF;labelWidth=145;spacingTop=5;"))
    geometry(item, x, y, 72, 72)


def add_badge(root: ET.Element, identifier: str, account: str, number: str, x: int, y: int) -> None:
    item = cell(root, id=f"step-{identifier}", value=number, vertex="1", parent=account,
                style=("ellipse;html=0;aspect=fixed;fillColor=#147EBA;strokeColor=#FFFFFF;"
                       "strokeWidth=2;fontFamily=Arial;fontSize=13;fontStyle=1;fontColor=#FFFFFF;"
                       "align=center;verticalAlign=middle;"))
    geometry(item, x, y, 28, 28)


def add_edge(root: ET.Element, source: str, target: str, index: int) -> None:
    label = EDGE_LABELS.get((source, target), "")
    cross_account = source == "aws_lambda_function.l3_export_gate"
    secondary = ((source == "aws_s3_bucket.l3_customer_evidence" and target == "tv_aws_textract.ocr")
                 or target == "aws_sqs_queue.intake_dlq")
    style = ("edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=0;"
             "endArrow=block;endFill=1;strokeColor=#545B64;strokeWidth=2;"
             "fontFamily=Arial;fontSize=12;fontColor=#545B64;labelBackgroundColor=#FFFFFF;")
    if cross_account:
        style += "strokeColor=#147EBA;strokeWidth=3;exitX=1;exitY=0.5;entryX=0;entryY=0.5;"
    if secondary:
        style += "dashed=1;dashPattern=5 4;strokeWidth=1;"
    if (source, target) in WAYPOINTS:
        style += "exitX=0.5;exitY=1;entryX=0.5;entryY=1;"
    if source in {"aws_cloudwatch_event_bus.results", "aws_sqs_queue.intake", "aws_lambda_function.receiver"}:
        style += "exitX=1;exitY=0.5;entryX=0;entryY=0.5;"
    item = cell(root, id=f"flow-{index:02d}", value=label, edge="1", parent="1",
                source=source, target=target, style=style)
    shape = ET.SubElement(item, "mxGeometry", {"relative": "1", "as": "geometry"})
    if (source, target) in WAYPOINTS:
        points = ET.SubElement(shape, "Array", {"as": "points"})
        for x, y in WAYPOINTS[source, target]:
            ET.SubElement(points, "mxPoint", {"x": str(x), "y": str(y)})


def main() -> None:
    graph = json.loads(GRAPH_PATH.read_text(encoding="utf-8"))
    expected = set(ACCOUNTS) | set(NODES)
    if set(graph) != expected:
        raise ValueError(f"Graph/node inventory differs: {set(graph) ^ expected}")
    for account in ACCOUNTS:
        listed = set(graph[account])
        placed = {key for key, spec in NODES.items() if spec[0] == account}
        if listed != placed:
            raise ValueError(f"Account contents differ: {account}: {listed ^ placed}")
    edges = [(source, target) for source, targets in graph.items()
             if source not in ACCOUNTS for target in targets]
    if any(target not in NODES for _, target in edges):
        raise ValueError("Graph contains an unknown connection target")

    document = ET.Element("mxfile", {"host": "app.diagrams.net", "type": "device", "pages": "1"})
    diagram = ET.SubElement(document, "diagram", {"id": "point-aws-architecture", "name": "AWS構成図"})
    model = ET.SubElement(diagram, "mxGraphModel", {
        "dx": "2400", "dy": "1100", "grid": "1", "gridSize": "10", "guides": "1",
        "tooltips": "1", "connect": "1", "arrows": "1", "fold": "1", "page": "1",
        "pageScale": "1", "pageWidth": "2400", "pageHeight": "1050", "math": "0", "shadow": "0",
    })
    root = ET.SubElement(model, "root")
    cell(root, id="0")
    cell(root, id="1", parent="0")

    add_text(root, "title", "解約金還元申請システム — AWS アーキテクチャ", 145, 20, 1900, 42, 26, True)
    add_cloud(root)
    for identifier, spec in ACCOUNTS.items():
        add_account(root, identifier, spec)
    for identifier, spec in GROUPS.items():
        add_group(root, identifier, spec)
    for index, (source, target) in enumerate(edges, start=1):
        add_edge(root, source, target, index)
    for identifier, spec in NODES.items():
        add_node(root, identifier, spec)
    for identifier, (number, x, y) in STEP_BADGES.items():
        add_badge(root, identifier, NODES[identifier][0], number, x, y)
    add_text(root, "l3-policy", "顧客情報・証跡原本・OCR全文はL3アカウント内に保持", 220, 790, 900, 28, 14, True, "#545B64")
    add_text(root, "transfer-policy", "アカウント間連携: マスク済みの許可項目のみ", 1210, 875, 700, 28, 14, True, "#147EBA", "center")
    add_text(root, "footer", "注: 追加予定の構成を含む論理構成図です。実際のデプロイ状態を示すものではありません。", 145, 1000, 1800, 26, 13, False, "#687078")

    ET.indent(document, space="  ")
    OUTPUT_PATH.write_bytes(ET.tostring(document, encoding="utf-8", xml_declaration=True))
    print(OUTPUT_PATH)


if __name__ == "__main__":
    main()
