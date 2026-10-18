#!/usr/bin/env python3
"""Generate the shared, editable AWS architecture diagram for diagrams.net.

The Terravision graph remains the inventory of components and connections. This
script assigns the same graph to a deliberate two-account layout using native
AWS shapes from the diagrams.net AWS4 library. No AWS credentials are needed.
"""

from __future__ import annotations

import json
from pathlib import Path
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parent.parent
GRAPH_PATH = ROOT / "docs" / "architecture.tvg.json"
OUTPUT_PATH = ROOT / "docs" / "architecture-aws.drawio"

# Coordinates are relative to the enclosing account frame. Icon labels are
# editable draw.io text, while service icons use the built-in AWS4 stencil.
ACCOUNTS = {
    "aws_account.l3_existing": ("AWS Account  |  L3アカウント（既存）", 260, 150, 2160, 590),
    "aws_account.management": ("AWS Account  |  管理システム用アカウント", 260, 805, 2160, 460),
}

NODES = {
    "tv_aws_internet.formrun": (None, None, "formrun\n申請・証跡", 35, 325, "#2D3142"),
    "tv_aws_users.reviewers": (None, None, "審査担当者", 35, 965, "#2D3142"),
    "aws_apigatewayv2_api.l3_webhook": ("aws_account.l3_existing", "api_gateway", "API Gateway\nWebhook受付", 115, 145, "#5A30B5"),
    "aws_lambda_function.l3_ingest": ("aws_account.l3_existing", "lambda", "受付Lambda\n申請・証跡取込", 355, 145, "#D05C17"),
    "aws_s3_bucket.l3_customer_evidence": ("aws_account.l3_existing", "s3", "S3\n顧客情報・証跡", 595, 145, "#277116"),
    "aws_sfn_state_machine.l3_review": ("aws_account.l3_existing", "step_functions", "Step Functions\n精査ワークフロー", 835, 145, "#BC1356"),
    "tv_aws_textract.ocr": ("aws_account.l3_existing", "textract", "Textract\n証跡抽出", 1075, 145, "#DD344C"),
    "aws_lambda_function.l3_identity": ("aws_account.l3_existing", "lambda", "本人確認Lambda\n契約者氏名と照合", 1315, 145, "#D05C17"),
    "aws_lambda_function.l3_award": ("aws_account.l3_existing", "lambda", "付与判定Lambda\nルール・AI判定", 1315, 385, "#D05C17"),
    "tv_aws_bedrock.judgement": ("aws_account.l3_existing", "bedrock", "Bedrock\n判定支援", 1555, 385, "#116D5B"),
    "aws_lambda_function.l3_export_gate": ("aws_account.l3_existing", "lambda", "持出ゲートLambda\n許可項目のみ送信", 1900, 270, "#D05C17"),
    "aws_cloudwatch_event_bus.results": ("aws_account.management", "eventbridge", "EventBridge\n結果イベント", 1900, 125, "#BC1356"),
    "aws_sqs_queue.intake": ("aws_account.management", "sqs", "SQS\n取込キュー", 1645, 125, "#BC1356"),
    "aws_sqs_queue.intake_dlq": ("aws_account.management", "sqs", "SQS DLQ\n再処理対象", 1645, 300, "#BC1356"),
    "aws_lambda_function.receiver": ("aws_account.management", "lambda", "受信Lambda\n版管理・保存", 1390, 125, "#D05C17"),
    "aws_dynamodb_table.applications": ("aws_account.management", "dynamodb", "DynamoDB\n申請・版履歴", 1135, 125, "#3334B9"),
    "aws_apigatewayv2_api.management": ("aws_account.management", "api_gateway", "API Gateway\n管理PUT / GET", 1390, 300, "#5A30B5"),
    "aws_cloudfront_distribution.admin": ("aws_account.management", "cloudfront", "CloudFront\n管理画面配信", 115, 125, "#5A30B5"),
    "aws_s3_bucket.admin_web": ("aws_account.management", "s3", "S3\n画面ファイル", 370, 125, "#277116"),
    "aws_cognito_user_pool.staff": ("aws_account.management", "cognito", "Cognito\n社内認証基盤", 625, 125, "#C7131F"),
}

EDGE_LABELS = {
    ("tv_aws_internet.formrun", "aws_apigatewayv2_api.l3_webhook"): "Webhook",
    ("aws_lambda_function.l3_ingest", "aws_s3_bucket.l3_customer_evidence"): "顧客情報・証跡を保存",
    ("aws_lambda_function.l3_ingest", "aws_sfn_state_machine.l3_review"): "保存後に開始",
    ("aws_s3_bucket.l3_customer_evidence", "tv_aws_textract.ocr"): "S3原本を参照",
    ("aws_lambda_function.l3_export_gate", "aws_cloudwatch_event_bus.results"): "持出許可済みの結果のみ",
    ("aws_sqs_queue.intake", "aws_sqs_queue.intake_dlq"): "失敗時",
}

# Long connections use separate clear lanes below the first processing row.
# These points are absolute coordinates on the draw.io page.
WAYPOINTS = {
    ("aws_lambda_function.l3_ingest", "aws_sfn_state_machine.l3_review"):
        [(656, 500), (1136, 500)],
    ("aws_s3_bucket.l3_customer_evidence", "tv_aws_textract.ocr"):
        [(896, 620), (1376, 620)],
    ("aws_lambda_function.l3_award", "aws_lambda_function.l3_export_gate"):
        [(1616, 700), (2201, 700)],
}


def cell(root: ET.Element, **attributes: str) -> ET.Element:
    return ET.SubElement(root, "mxCell", attributes)


def geometry(parent: ET.Element, x: int, y: int, width: int, height: int) -> None:
    ET.SubElement(parent, "mxGeometry", {
        "x": str(x), "y": str(y), "width": str(width),
        "height": str(height), "as": "geometry",
    })


def add_note(root: ET.Element, identifier: str, value: str, x: int, y: int,
             width: int, height: int, font_size: int, color: str) -> None:
    item = cell(root, id=identifier, value=value, vertex="1", parent="1",
                style=("text;html=0;whiteSpace=wrap;align=left;verticalAlign=middle;"
                       f"fontFamily=Arial;fontSize={font_size};fontStyle=1;fontColor={color};"
                       "strokeColor=none;fillColor=none;"))
    geometry(item, x, y, width, height)


def add_account(root: ET.Element, identifier: str, spec: tuple) -> None:
    label, x, y, width, height = spec
    fill = "#F4F9FD" if identifier.endswith("l3_existing") else "#F8FAFC"
    stroke = "#356890" if identifier.endswith("l3_existing") else "#67778A"
    item = cell(root, id=identifier, value=label, vertex="1", parent="1",
                style=("swimlane;container=1;collapsible=0;recursiveResize=0;"
                       "startSize=62;horizontal=1;rounded=0;html=0;"
                       f"fillColor={fill};swimlaneFillColor={fill};strokeColor={stroke};"
                       "strokeWidth=3;fontFamily=Arial;fontSize=25;fontStyle=1;"
                       "fontColor=#232F3E;align=left;spacingLeft=30;"
                       "verticalAlign=top;spacingTop=13;"))
    geometry(item, x, y, width, height)


def add_edge(root: ET.Element, source: str, target: str, index: int) -> None:
    label = EDGE_LABELS.get((source, target), "")
    crossing = source == "aws_lambda_function.l3_export_gate"
    reference = source == "aws_s3_bucket.l3_customer_evidence" and target == "tv_aws_textract.ocr"
    failure = target == "aws_sqs_queue.intake_dlq"
    color = "#2E5AA8" if crossing else "#64748B"
    style = ("edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;"
             "jettySize=auto;html=0;endArrow=block;endFill=1;"
             f"strokeColor={color};strokeWidth={'3' if crossing else '2'};"
             "fontFamily=Arial;fontSize=14;fontColor=#334155;"
             "labelBackgroundColor=#FFFFFF;")
    if reference or failure:
        style += "dashed=1;dashPattern=5 4;"
    if (source == "aws_cloudwatch_event_bus.results"
            or (source == "aws_sqs_queue.intake" and not failure)
            or source == "aws_lambda_function.receiver"):
        style += "exitX=0;exitY=0.5;entryX=1;entryY=0.5;"
    if (source, target) in WAYPOINTS:
        style += "exitX=0.5;exitY=1;entryX=0.5;entryY=1;"
    if crossing:
        style += "exitX=0.5;exitY=1;entryX=0.5;entryY=0;"
    item = cell(root, id=f"flow-{index:02d}", value=label, edge="1", parent="1",
                source=source, target=target, style=style)
    shape = ET.SubElement(item, "mxGeometry", {"relative": "1", "as": "geometry"})
    if (source, target) in WAYPOINTS:
        points = ET.SubElement(shape, "Array", {"as": "points"})
        for x, y in WAYPOINTS[source, target]:
            ET.SubElement(points, "mxPoint", {"x": str(x), "y": str(y)})


def add_node(root: ET.Element, identifier: str, spec: tuple) -> None:
    account, icon, label, x, y, color = spec
    if account is None:
        item = cell(root, id=identifier, value=label, vertex="1", parent="1",
                    style=("rounded=1;arcSize=8;whiteSpace=wrap;html=0;"
                           "align=center;verticalAlign=middle;"
                           "fontFamily=Arial;fontSize=20;fontStyle=1;"
                           "fontColor=#232F3E;fillColor=#FFFFFF;"
                           "strokeColor=#94A3B8;strokeWidth=2;"))
        geometry(item, x, y, 185, 100)
        return

    item = cell(root, id=identifier, value=label, vertex="1", parent=account,
                style=("sketch=0;outlineConnect=0;gradientColor=none;"
                       f"fillColor={color};strokeColor=#FFFFFF;"
                       "shape=mxgraph.aws4.resourceIcon;"
                       f"resIcon=mxgraph.aws4.{icon};"
                       "aspect=fixed;html=0;whiteSpace=wrap;"
                       "verticalLabelPosition=bottom;verticalAlign=top;align=center;"
                       "fontFamily=Arial;fontSize=17;fontStyle=1;fontColor=#232F3E;"
                       "labelBackgroundColor=#FFFFFF;labelWidth=210;spacingTop=6;"))
    geometry(item, x, y, 82, 82)


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
    cross_account = [(source, target) for source, target in edges
                     if NODES[source][0] in ACCOUNTS and NODES[target][0] in ACCOUNTS
                     and NODES[source][0] != NODES[target][0]]
    if cross_account != [("aws_lambda_function.l3_export_gate", "aws_cloudwatch_event_bus.results")]:
        raise ValueError("Unexpected cross-account data path")

    document = ET.Element("mxfile", {"host": "app.diagrams.net", "type": "device",
                                     "pages": "1"})
    diagram = ET.SubElement(document, "diagram", {"id": "point-aws-architecture",
                                                  "name": "AWS構成図"})
    model = ET.SubElement(diagram, "mxGraphModel", {
        "dx": "2400", "dy": "1300", "grid": "1", "gridSize": "10",
        "guides": "1", "tooltips": "1", "connect": "1", "arrows": "1",
        "fold": "1", "page": "1", "pageScale": "1", "pageWidth": "2480",
        "pageHeight": "1320", "math": "0", "shadow": "0",
    })
    root = ET.SubElement(model, "root")
    cell(root, id="0")
    cell(root, id="1", parent="0")

    add_note(root, "title", "解約金還元申請システム  |  AWS構成図", 55, 38, 1700, 50, 34, "#232F3E")
    add_note(root, "subtitle", "L3内で顧客情報と証跡を処理し、許可済みの結果のみ管理側へ連携", 57, 93, 1800, 34, 17, "#4F5D75")
    for identifier, spec in ACCOUNTS.items():
        add_account(root, identifier, spec)
    for index, (source, target) in enumerate(edges, start=1):
        add_edge(root, source, target, index)
    for identifier, spec in NODES.items():
        add_node(root, identifier, spec)
    add_note(root, "l3-note", "顧客情報・証跡原本・OCR全文はL3内に保持", 340, 675, 850, 34, 16, "#356890")
    add_note(root, "transfer-note", "AWS Account間の連携  |  マスク済みの許可項目だけ", 1470, 755, 900, 36, 17, "#2E5AA8")
    add_note(root, "footer", "設計図：追加予定の構成を含む。AWSアカウントやリソースの作成状態を示すものではありません。", 58, 1278, 2100, 30, 15, "#4F5D75")

    ET.indent(document, space="  ")
    OUTPUT_PATH.write_bytes(ET.tostring(document, encoding="utf-8", xml_declaration=True))
    print(OUTPUT_PATH)


if __name__ == "__main__":
    main()
