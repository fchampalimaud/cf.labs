using Bonsai;
using System;
using System.ComponentModel;
using System.Collections.Generic;
using System.Linq;
using System.Reactive.Linq;
using Bonsai.Vision;

[Combinator]
[Description("")]
[WorkflowElementCategory(ElementCategory.Transform)]
public class TransformScript
{
    public IObservable<RegionActivityCollection> Process(IObservable<RegionActivityCollection> source)
    {
        return source.Select(value => value);
    }
}
