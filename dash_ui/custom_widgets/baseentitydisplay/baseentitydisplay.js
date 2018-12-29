function baseentitydisplay(widget_id, url, skin, parameters)
{
    // Will be using "self" throughout for the various flavors of "this"
    // so for consistency ...

    self = this;

    // Initialization

    self.widget_id = widget_id;

    // Store on brightness or fallback to a default

    // Parameters may come in useful later on

    self.parameters = parameters;

    var callbacks = [];

    // Define callbacks for entities - this model allows a widget to monitor multiple entities if needed
    // Initial will be called when the dashboard loads and state has been gathered for the entity
    // Update will be called every time an update occurs for that entity

    self.OnTitleStateAvailable = OnTitleStateAvailable;
    self.OnTitleStateUpdate = OnTitleStateUpdate;
    self.OnTitle2StateAvailable = OnTitle2StateAvailable;
    self.OnTitle2StateUpdate = OnTitle2StateUpdate;
    self.OnStateAvailable = OnStateAvailable;
    self.OnStateUpdate = OnStateUpdate;
    self.OnSubStateAvailable = OnSubStateAvailable;
    self.OnSubStateUpdate = OnSubStateUpdate;

    var monitored_entities =  [];

	if ("entity" in parameters && parameters.entity != "")
    {
        // Check if the sub_entity should be created by monitoring an attribute of the entity
        if ("entity_to_sub_entity_attribute" in parameters && parameters.entity_to_sub_entity_attribute != "")
        {
            self.sub_entity = parameters.entity;
            self.sub_entity_attribute = parameters.entity_to_sub_entity_attribute;
        }
		// Check if the title2_entity should be created by monitoring an attribute of the entity
        if ("entity_to_title2_entity_attribute" in parameters && parameters.entity_to_title2_entity_attribute != "")
        {
            self.title2_entity = parameters.entity;
            self.title2_entity_attribute = parameters.entity_to_title2_entity_attribute;
        }
    }
    // Only set up the sub_entity if it was not created already with the entity + attribute
    if ("sub_entity" in parameters && parameters.sub_entity != "" && !("sub_entity" in self))
    {
        // Make sure that we monitor the sub_entity, not an attribute of it
        self.sub_entity = parameters.sub_entity;
    }
	// Only set up the title2_entity if it was not created already with the entity + attribute
    if ("title2_entity" in parameters && parameters.title2_entity != "" && !("title2_entity" in self))
    {
        // Make sure that we monitor the sub_entity, not an attribute of it
        self.title2_entity = parameters.title2_entity;
    }

    if ("title_entity" in parameters && parameters.title_entity != "")
    {
        monitored_entities.push({"entity": parameters.title_entity, "initial": self.OnTitleStateAvailable, "update": self.OnTitleStateUpdate});
    }
    if ("title2_entity" in self)
    {
        monitored_entities.push({"entity": self.title2_entity, "initial": self.OnTitle2StateAvailable, "update": self.OnTitle2StateUpdate});
    }
    if ("entity" in parameters)
    {
        monitored_entities.push({"entity": parameters.entity, "initial": self.OnStateAvailable, "update": self.OnStateUpdate});
    }
    if ("sub_entity" in self)
    {
        monitored_entities.push({"entity": self.sub_entity, "initial": self.OnSubStateAvailable, "update": self.OnSubStateUpdate});
    }

    // Finally, call the parent constructor to get things moving

    WidgetBase.call(self, widget_id, url, skin, parameters, monitored_entities, callbacks);

    // Function Definitions

    // The StateAvailable function will be called when
    // self.state[<entity>] has valid information for the requested entity
    // state is the initial state
    // Methods

    function OnTitleStateAvailable(self, state)
    {
        set_title_value(self, state);
    }

    function OnTitleStateUpdate(self, state)
    {
        set_title_value(self, state);
    }

    function OnTitle2StateAvailable(self, state)
    {
        set_title2_value(self, state);
    }

    function OnTitle2StateUpdate(self, state)
    {
        set_title2_value(self, state);
    }

    function OnStateAvailable(self, state)
    {
        set_value(self, state);
    }

    function OnStateUpdate(self, state)
    {
        set_value(self, state);
    }

    function OnSubStateAvailable(self, state)
    {
        set_sub_value(self, state);
    }

    function OnSubStateUpdate(self, state)
    {
        set_sub_value(self, state);
    }

    function set_title_value(self, state)
    {
        self.set_field(self, "title", state.state);
    }

    function set_title2_value(self, state)
    {
		if ("title2_entity_attribute" in self && self.title2_entity_attribute != "")
        {
            value = state.attributes[self.title2_entity_attribute];
        }
        else
        {
            value = state.state;
        }
        self.set_field(self, "title2", value);
    }

    function set_value(self, state)
    {
        value = self.map_state(self, state.state);
        if (isNaN(value))
        {
            self.set_field(self, "value_style", self.parameters.css.text_style);
            self.set_field(self, "value", self.map_state(self, value));
        }
        else
        {
            self.set_field(self, "value_style", self.parameters.css.value_style);
            self.set_field(self, "value", self.format_number(self, value));
            self.set_field(self, "unit_style", self.parameters.css.unit_style);
            if ("units" in self.parameters)
            {
                self.set_field(self, "unit", self.parameters.units);
            }
            else
            {
                self.set_field(self, "unit", state.attributes["unit_of_measurement"]);
            }
        }
    }

    function set_sub_value(self, state)
    {
		if ("sub_entity_attribute" in self && self.sub_entity_attribute != "")
        {
            statevalue = state.attributes[self.sub_entity_attribute];
        }
        else
        {
            statevalue = state.state;
        }

        if ("sub_entity_map" in self.parameters)
        {
            self.set_field(self, "state_text", self.parameters.sub_entity_map[statevalue]);
        }
        else
        {
            value = self.map_state(self, statevalue);
            if (isNaN(value))
            {
                self.set_field(self, "state_text", statevalue);
            }
            else
            {
                self.set_field(self, 'state_text',
                    self.format_number(self, value) +
                    (state.attributes.unit_of_measurement ?
                        ' ' + state.attributes.unit_of_measurement :
                        ''
                    )
                );
            }
        }
    }

}
