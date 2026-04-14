from app.services.action_item_postprocess import clean_action_items


def test_clean_action_items_filters_and_rewrites():
    raw = [
        "We — will keep one backup meeting already processed before any live demo",
        "Lalita — will create the clean 10-minute audio test and run it through the product today",
        "For the 10-minute test file, we should include a business-style conversation with a product update, a target audience discussion, a pilot decision, outreach actions, and a deadline for the next step",
        "The landing page and outreach message will be reviewed and finalized by Friday",
        "Let's make that an action item as well",
    ]

    cleaned = clean_action_items(raw)

    assert "Let's make that an action item as well" not in cleaned
    assert "Team - keep one backup meeting already processed before any live demo" in cleaned
    assert "Lalita - create the clean 10-minute audio test" in cleaned
    assert "Lalita - run it through the product today" in cleaned
    assert not any("we should include" in x.lower() for x in cleaned)
    assert "Team - review and finalize landing page and outreach message (due: by Friday)" in cleaned
