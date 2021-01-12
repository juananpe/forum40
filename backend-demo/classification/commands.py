import click

from classification.train import train
from classification.update import update


@click.group()
def classification():
    pass


@classification.command('train', help='Classifier trainer')
@click.argument('source-id', required=True, type=int)
@click.option('--labelname', required=True, help='Name of the category for model training')
@click.option('--optimize', is_flag=True, help='Run C parameter optimization')
@click.option('--cv', is_flag=True, help='Perform cross validation after training')
def cli_train(source_id: int, labelname: str, optimize: bool, cv: bool):
    train(labelname=labelname, optimize=optimize, cv=cv)


@classification.command('update', help='Update category labels')
@click.argument('source-id', required=True, type=int)
@click.option('--labelname', required=True, help='Name of the category for model training')
@click.option('--skip-confidence', is_flag=True, help='Update changing labels only')
@click.option('--optimize', is_flag=True, help='Run C parameter optimization')
@click.option('--init-facts-only', is_flag=True, help='Do not predict anything, but init the fact table for a label')
@click.option('--skip-train', is_flag=True, help='Skip retraining model')
def cli_update(source_id: int, labelname: str, skip_confidence: bool, optimize: bool, init_facts_only: bool, skip_train: bool):
    update(
        source_id=source_id, labelname=labelname, skip_confidence=skip_confidence,
        optimize=optimize, init_facts_only=init_facts_only, skip_train=skip_train,
    )
